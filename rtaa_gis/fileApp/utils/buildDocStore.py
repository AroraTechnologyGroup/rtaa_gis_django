import os
import mimetypes
import sys
import django
import requests
import logging
import json
import traceback
import pyodbc
import datetime
from django.core.exceptions import ObjectDoesNotExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rtaa_gis.settings'
django.setup()

from fileApp.models import EngineeringFileModel, EngineeringAssignment, GridCell,\
    DisciplineModel, SheetTypeModel, DocumentTypeModel

from fileApp.serializers import EngSerializer, EngAssignmentSerializer
from fileApp.utils.domains import FileTypes
from fileApp.utils import function_definitions
from django.conf import settings

TOP_DIRs = settings.FILE_APP_TOP_DIRS

acc_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures/data/reno.accdb")

# for testing load the sample pdf files
# test_dir = os.path.join(settings.BASE_DIR, "fileApp/fixtures/data")
# TOP_DIRs = [test_dir]
# acc_db_path = test_dir


class Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class FileStoreBuilder:
    def __init__(self):
        self.top_dirs = TOP_DIRs
        self.FileTypes = FileTypes()
        pass

    @staticmethod
    def format_text(input):
        string = input.strip().capitalize()
        return string

    def build_rel_stores(self):
        for x in self.FileTypes.DOC_VIEWER_TYPES:
            try:
                DocumentTypeModel.objects.get(name=x[0])
            except ObjectDoesNotExist:
                name = x[0]
                label = x[1]
                obj = DocumentTypeModel.objects.create(name=name, label=label)
                obj.save()

        for x in self.FileTypes.engineering_sheet_types:
            try:
                SheetTypeModel.objects.get(name=x[0])
            except ObjectDoesNotExist:
                name = x[0]
                label = x[1]
                obj = SheetTypeModel.objects.create(name=name, label=label)
                obj.save()

        for x in self.FileTypes.engineering_discipline_choices:
            try:
                DisciplineModel.objects.get(name=x[0])
            except ObjectDoesNotExist:
                name = x[0]
                label = x[1]
                obj = DisciplineModel.objects.create(name=name, label=label)
                obj.save()

    def load_accdb(self):
        # write file paths from Tiffany that cannot be found
        no_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no_match.txt")
        yes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yes_match.txt")
        noFile = open(no_file, 'w')
        yesFile = open(yes_file, 'w')

        try:
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=%s;' % acc_db_path
            )
            cnxn = pyodbc.connect(conn_str)
            cursor = cnxn.cursor()
            cursor.execute("SELECT FILENAME, SHEETTYPE, DISCIPLINE, PROJECTNAME, SHEETDESCRIPTION,"
                           "SHEETNUMBER, DATE, VENDOR FROM reno")
            rows = cursor.fetchall()
            for row in rows:
                if row[-1] != 'text':
                    file_path, sheet_type, discipline, project_title, sheet_description, sheet_title, project_date, vendor = row
                    file_path = file_path.replace('#', '')
                    file_path = file_path.lstrip(r"i:\\")
                    file_path = r"//renofs2/groups/" + file_path
                    file_path = file_path.replace("\\", "/")
                    file_path = file_path.lower()

                    if not file_path:
                        file_path = ""

                    if not vendor:
                        vendor = ""
                    else:
                        vendor = self.format_text(vendor)

                    if project_date:
                        project_date = datetime.date(int(project_date), 1, 1)
                    else:
                        project_date = datetime.date(9999, 1, 1)

                    if not sheet_title:
                        sheet_title = ""
                    else:
                        sheet_title = self.format_text(sheet_title)

                    if not sheet_type:
                        sheet_type = ["unk"]
                    else:
                        sheet_types = sheet_type.strip().lower().split()
                        sheet_types = [x.strip() for x in sheet_types]

                        sheet_type_lookup = {
                            "quantity": ["quantity"],
                            "title": ["title"],
                            "key": ["key"],
                            "index": ["index"],
                            "details": ["detail"],
                            "symbols": ["symbol"],
                            "specifications": ["specification"],
                            "schedule": ["schedule"],
                            "sections": ["section"],
                            "plan": ["plan"],
                            "notes": ["note"],
                            "elevations": ["elevation"],
                            "diagram": ["diagram"],
                        }

                        new_list = []
                        for s_type in sheet_types:
                            # the accdb has types combined without spaces and with slashes.
                            # this should find each type by checking whether it is in the string
                            for k, v in iter(sheet_type_lookup.items()):
                                if v[0] in s_type:
                                    new_list.append(k)
                        sheet_type = new_list

                    if not discipline:
                        discipline = ["unk"]
                    else:
                        disciplines = discipline.strip().lower().split()
                        disciplines = [x.strip() for x in disciplines]

                        discipline_lookup = {
                            "misc": ["miscellaneous", "misc"],
                            "civil": ["civil"],
                            "arch": ["architectural", "arch"],
                            "structural": ["structural"],
                            "landscaping": ["landscaping", "landscape"],
                            "mechanical-hvac": ["mechanical(hvac)"],
                            "plumbing": ["plumbing"],
                            "electrical": ["electrical", "electricals", "electric"],
                            "mechanical": ["mechanical"],
                            "fire protection": ["fire protection"]
                        }
                        new_list = []
                        for disc in disciplines:
                            for k, v in iter(discipline_lookup.items()):
                                if disc in v:
                                    new_list.append(k)

                        discipline = new_list

                    if not project_title:
                        project_title = ""
                    else:
                        project_title = self.format_text(project_title)

                    if not sheet_description:
                        sheet_description = ""
                    else:
                        sheet_description = self.format_text(sheet_description)

                    # All File Paths in the system are in lower case
                    filtered = EngineeringFileModel.objects.filter(file_path=file_path)
                    if len(filtered) == 0:
                        # The file object was not located in the fileStore using the file_path

                        new_obj = {
                            'file_path': file_path,
                            'sheet_type': sheet_type,
                            'discipline': discipline,
                            'project_title': project_title,
                            'sheet_description': sheet_description,
                            'sheet_title': sheet_title,
                            'project_date': project_date,
                            'document_type': ['unk'],
                            'vendor': vendor,
                            'airport': '',
                            'project_description': '',
                            'funding_type': '',
                            'grant_number': '',
                            'comment': ''
                        }
                        try:
                            ser_obj = EngSerializer(data=new_obj)
                            if ser_obj.is_valid():
                                noFile.write("path: {}\n".format(ser_obj.validated_data["file_path"]))
                                noFile.write("discipline: {}\n".format(ser_obj.validated_data["discipline"]))
                                noFile.write("project_title: {}\n".format(ser_obj.validated_data["project_title"]))
                                noFile.write("sheet_type: {}\n".format(ser_obj.validated_data["sheet_type"]))
                                noFile.write("sheet_title: {}\n\n".format(ser_obj.validated_data["sheet_title"]))
                                pass
                            else:
                                print(ser_obj.errors)
                        except:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)

                    elif len(filtered) == 1:
                        # The file was matched to a record in the database
                        _object = filtered[0]
                        doc_types = _object.document_type.all()
                        airport = _object.airport
                        project_description = _object.project_description
                        funding_type = _object.funding_type
                        grant_number = _object.grant_number
                        comment = _object.comment

                        update_data = {
                            "file_path": file_path,
                            "sheet_type": sheet_type,
                            "discipline": discipline,
                            "project_title": project_title,
                            "sheet_description": sheet_description,
                            "sheet_title": sheet_title,
                            "project_date": project_date,
                            "document_type": doc_types,
                            "vendor": vendor,
                            "airport": airport,
                            "project_description": project_description,
                            "funding_type": funding_type,
                            "grant_number": grant_number,
                            "comment": comment
                        }

                        try:
                            new_s = EngSerializer(_object, data=update_data, partial=True)
                            if new_s.is_valid():
                                yesFile.write("path: {}\n".format(new_s.validated_data["file_path"]))
                                yesFile.write("discipline: {}\n".format(new_s.validated_data["discipline"]))
                                yesFile.write("project_title: {}\n".format(new_s.validated_data["project_title"]))
                                yesFile.write("sheet_type: {}\n".format(new_s.validated_data["sheet_type"]))
                                yesFile.write("sheet_title: {}\n\n".format(new_s.validated_data["sheet_title"]))
                                new_s.save()
                            else:
                                print(new_s.errors)
                        except Exception as e:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                            print(e)

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        noFile.close()
        yesFile.close()

    def build_store(self):
        try:
            top_dirs = self.top_dirs
            file_types = self.FileTypes
            for top_dir in top_dirs:
                # The airport is determined by the root folder the file is found under
                if top_dir.lower().endswith("rno"):
                    airport = "rno"
                elif top_dir.lower().endswith("std"):
                    airport = "rts"
                else:
                    raise Exception("Airport could not be determined from the last directory in top dir file path {}".format(top_dir))

                for root, dirs, files in os.walk(top_dir):
                    for _file in files:

                        for mapping in iter(file_types.ALL_FILE_TYPES.keys()):
                            # there is only one key for each mapping dict so testing
                            # if the extension is IN the dict as a key is good enough
                            # This basically limits the types of files we are including
                            extension = _file.split(".")[-1].lower()
                            if extension == mapping:
                                file_path = os.path.join(root, _file)
                                file_path = file_path.replace("\\", "/")
                                # all file_paths in the system are lower case
                                file_path = file_path.lower()
                                filtered = EngineeringFileModel.objects.filter(file_path=file_path)
                                if len(filtered) == 0:
                                    # File has not been added to the database
                                    ser = EngSerializer(data={
                                        "file_path": file_path,
                                        "airport": airport
                                    })
                                    if ser.is_valid():
                                        ser.save()
                                    else:
                                        logging.error(ser.errors)

                                elif len(filtered) == 1:
                                    # The File Exists in the Database and will be updated
                                    _object = filtered[0]
                                    serializer = EngSerializer(_object, data={
                                        "file_path": file_path,
                                        "airport": airport
                                    }, partial=True)
                                    if serializer.is_valid():
                                        serializer.save()
                                    else:
                                        logging.error(serializer.errors)

        except Exception as e:
            logging.warning(e)

        return

    def clean_store(self):
        """Remove paths that don't exist;
        Remove directories;
        remove paths that don't match with TOP_DIRs;
       """
        def check_roots(in_path, roots):
            d = False
            lower_path = in_path.lower().replace("\\", "/")
            for x in roots:
                lower_root = x.lower().replace("\\", "/")
                if lower_path.startswith(lower_root):
                    if os.path.exists(in_path):
                        if not os.path.isdir(in_path):
                            # remove any files with "\" in the path, these will cause duplication
                            try:
                                in_path.index("\\")
                                d = False
                            except ValueError:
                                d = True
            return d

        try:
            file_paths = []
            for _file in EngineeringFileModel.objects.all():
                path = _file.file_path
                if not check_roots(path, self.top_dirs):
                    _file.delete()

                else:
                    if path not in file_paths:
                        file_paths.append(path)
                    else:
                        raise Error("Duplicate file objects with path {}".format(path))
                        pass

        except Exception as e:
            print(e)


class GridCellBuilder:
    def __init__(self):
        pass

    @staticmethod
    def build_store():
        """This will create new grid cell rows only if they dont exist"""
        # send query request to esri rest api
        login_params = {
            'client_id': 'iVMcOt2MrFfgmRBF',
            'client_secret': 'e6df1381878a49e8b3df8e5c654c0110',
            'grant_type': 'client_credentials'
        }

        token = requests.get('https://www.arcgis.com/sharing/rest/oauth2/token/',
                              params=login_params)
        access_token = token.json()['access_token']

        query_url = r'https://services6.arcgis.com/GC5xdlDk2dEYWofH/arcgis/rest/services/Airfield_Grid/FeatureServer/1/query'
        query_params = {
            'f': 'json',
            'token': access_token,
            'returnM': 'false',
            'returnZ': 'false',
            'returnDistinctValues': 'true',
            'returnGeometry': 'false',
            'outFields': 'GRID',
            'where': "Id LIKE '%'"
        }

        feature_service = requests.post(query_url, params=query_params)

        features = feature_service.json()['features']
        for feature in features:

            grid = feature['attributes']['GRID']
            name = '{}'.format(grid)
            try:
                filtered = GridCell.objects.filter(name=name)
                # Only create a grid cell if one with that name does not exist
                if len(filtered) == 0:
                    x = GridCell.objects.create(name=name)
                    x.save()
                else:
                    pass

            except Exception as e:
                logging.error("Error populating the Grid Model {}".format(name))
                print(e)


class AssignmentManager:
    def __init__(self):
        pass

    def clear(self, data):
        pass

    @staticmethod
    def create_test_assignments():
        files = EngineeringFileModel.objects.all()
        grid_cells = GridCell.objects.all()
        i = 0
        for file in files:
            try:
                grid_cell = grid_cells[i]
                new_obj = {
                    "file": "http://127.0.0.1:8080/fileApp/eng-files/{}/".format(file.pk),
                    "grid_cell": grid_cell.name
                }
                i += 3

                try:
                    existing = EngineeringAssignment.objects.filter(grid_cell=grid_cell).filter(file=file)
                    if len(existing):
                        check = EngAssignmentSerializer(existing[0], data=new_obj)
                    else:
                        check = EngAssignmentSerializer(data=new_obj)

                    if check.is_valid():
                        check.save()

                    else:
                        print("{} and {} could not be assigned".format(grid_cell, file.base_name))
                except Exception:
                    print(Exception)

            except IndexError:
                pass


if __name__ == '__main__':
    x = FileStoreBuilder()
    x.build_rel_stores()
    x.clean_store()
    x.build_store()
    if os.path.exists(acc_db_path):
        x.load_accdb()
    cell = GridCellBuilder()
    cell.build_store()

