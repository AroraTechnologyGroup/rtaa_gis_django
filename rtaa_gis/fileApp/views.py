import os
import sys
import logging
import traceback

from .utils import buildDocStore
from home.utils.ldap_tool import LDAPQuery
from analytics.serializers import RecordSerializer
from .serializers import GridSerializer, EngAssignmentSerializer, EngSerializer, FileTypes
from .models import GridCell, EngineeringFileModel, EngineeringAssignment
from .pagination import LargeResultsSetPagination, StandardResultsSetPagination
from .forms import FilterForm
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.decorators import detail_route, list_route, permission_classes, api_view, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.reverse import reverse_lazy
from rest_framework import response, schemas
from rest_framework_jsonp.renderers import JSONRenderer
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView
from .utils import WatchDogTrainer
from .utils.OOoConversion import OpenOfficeConverter
from django.http import HttpResponse
from django.core.files import File
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User, Group

from PIL import Image
import platform
if platform.system() == 'Windows':
    import win32com.client
    import pythoncom
    pass

MEDIA_ROOT = settings.MEDIA_ROOT
BASE_DIR = settings.BASE_DIR
LOGIN_URL = settings.LOGIN_URL
LOGIN_REDIRECT_URL = settings.LOGIN_REDIRECT_URL
FILE_APP_TOP_DIRS = settings.FILE_APP_TOP_DIRS

logger = logging.getLogger(__name__)
trainer = WatchDogTrainer.Observers(FILE_APP_TOP_DIRS)


def log_traceback():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return repr(traceback.format_exception(exc_type, exc_value, exc_traceback))


def create_response_object(in_path, extension):
    """generates a pdf file like object and writes to an http response"""

    def create_image_object(file_path):
        """generate an in memory image object that will be returned via HTTP"""
        fil = File(open(file_path, 'rb'))
        im = Image.open(fil)
        resp = HttpResponse(content_type="image/png")
        im.save(resp, 'PNG')
        fil.close()
        return resp

    pythoncom.CoInitialize()
    response = HttpResponse(content_type='application/pdf')
    if extension == 'pdf':
        """These files are already in an acceptable format"""
        fp = File(open(in_path, 'rb'))
        response.write(fp.read())
        fp.close()

    elif extension in FileTypes.DOC_VIEWER_TYPES:
        # TODO MSWORD Documents should not be written to the hard drive
        try:
            temp_location = "{}\\{}".format(MEDIA_ROOT, "_fileApp")
            basename = os.path.basename(in_path).replace(extension, "pdf")
            temp_path = "{}\\{}".format(temp_location, basename)
            word = win32com.client.DispatchEx("Word.Application")

            doc = word.Documents.Open(in_path)
            # 17 is pdf
            doc.SaveAs2(format(temp_path), FileFormat=17)
            doc.Close()
            word.Quit()
            del word
            del doc

            f = File(open(temp_path, 'rb'))
            response.write(f.read())
            f.close()
            os.remove(temp_path)

        except Exception as e:
            """Create the Open Office Conversion class that calls the
            conversion scripts that exist in the Open Office program directory"""
            o_doc = OpenOfficeConverter(in_path)
            response = o_doc.convert()

    elif extension in FileTypes.TABLE_VIEWER_TYPES:
        # TODO MSEXCEL File should not be written to the hard drive
        try:
            temp_location = "{}\\{}".format(MEDIA_ROOT, "_fileApp")
            basename = os.path.basename(in_path).replace(extension, "pdf")
            temp_path = "{}\\{}".format(temp_location, basename)

            xl = win32com.client.DispatchEx("Excel.Application")
            xl.Application.AskToUpdateLinks = 0
            wb = xl.Workbooks.Open(in_path)
            # 17 is pdf
            wb.SaveAs2(temp_path, FileFormat=17)
            wb.Close()
            xl.Quit()
            del xl
            del wb

            f = File(open(temp_path, 'rb'))
            response.write(f.read())
            f.close()
            os.remove(temp_path)

        except:
            o_doc = OpenOfficeConverter(in_path)
            response = o_doc.convert()
            pass

    elif extension in FileTypes.IMAGE_VIEWER_TYPES:
        """This response changes the content_type to image/png"""
        response = create_image_object(in_path)

    pythoncom.CoUninitialize()

    return response


def authorize_user(request, template):
    if not request.user.is_authenticated():
        return redirect(reverse('home:login'))
    try:
        name = request.META['REMOTE_USER']
    except KeyError:
        name = request.user.username

    resp = Response(template_name=template)
    resp['Cache-Control'] = 'no-cache'

    # Perform inheritance from AD
    local_name = name.split("\\")[-1]
    query = LDAPQuery(local_name, settings.LDAP_URL)
    ldap_groups = query.get_groups()
    logger.info("ldap_groups = {}".format(ldap_groups))
    logger.info("username = {}".format(name))

    user_obj = User.objects.get(username=name)
    users_groups = user_obj.groups.all()
    # remove groups from user if not in LDAP group list
    for x in users_groups:
        if x.name not in ldap_groups:
            try:
                g = Group.objects.get(name=x)
                user_obj.groups.remove(g)
                user_obj.save()
            except Exception as e:
                print(e)
    # add user to group if group exists in ldap and local group table
    for x in ldap_groups:
        if x not in [g.name for g in users_groups]:
            try:
                g = Group.objects.get(name=x)
                user_obj.groups.add(g)
                user_obj.save()
            except Exception as e:
                print(e)

    # Create user's folder in the media root
    users_dir = os.path.join(settings.MEDIA_ROOT, 'users')
    if not os.path.exists(users_dir):
        os.mkdir(users_dir)
    user_dir = os.path.join(users_dir, local_name)
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    # make the print directory for the user
    print_dir = os.path.join(user_dir, "prints")
    if not os.path.exists(print_dir):
        os.mkdir(print_dir)

    return [x.name for x in user_obj.groups.all()]



@method_decorator(ensure_csrf_cookie, name='dispatch')
class PagedFileViewSet(viewsets.ModelViewSet):
    """Paged view of file objects"""
    filter_fields = ('file_path', 'base_name', 'file_type', 'size', 'date_added')
    pagination_class = StandardResultsSetPagination

    @list_route(methods=['get',])
    def _stop_monitors(self, request):
        """Kill all of the watchdog monitor processes"""
        if request.user.is_authenticated():
            x = trainer.stop_monitors()
            return Response(x)
        else:
            return redirect(reverse('home:login'))

    @list_route(methods=['get',])
    def _start_monitors(self, request):
        """Start a watchdog monitor process for each of the paths in TOP_DIRs"""
        if request.user.is_authenticated():
            x = trainer.start_monitors()
            return Response(x)
        else:
            return redirect(reverse('home:login'))


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngGridViewSet(viewsets.ModelViewSet):
    """Grid Cells within the ArcGIS Online Map Grid"""
    queryset = GridCell.objects.all()
    serializer_class = GridSerializer
    filter_fields = ('name',)

    @detail_route()
    def _files(self, request, pk=None):
        """Files that have been assigned to the specified grid cell"""
        if request.user.is_authenticated():
            queryset = EngineeringAssignment.objects.filter(grid_cell_id__exact=str(pk))
            file_models = [x.file for x in queryset]
            serializer = EngSerializer(file_models, many=True)
            return Response(serializer.data)
        else:
            return redirect(reverse('home:login'))

    @list_route()
    def _build(self, request):
        """Logon to AGOL, query the grid cell service and build the grid cell data table in sqlite"""
        if request.user.is_authenticated():
            tool = buildDocStore.GridCellBuilder()
            tool.build_store()
            grids = GridCell.objects.all()
            serializer = GridSerializer(grids, many=True)
            return Response(serializer.data)
        else:
            return redirect(reverse('home:login'))


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngAssignmentViewSet(viewsets.ModelViewSet):
    """This view is used to manage the assignments of files to grid cells"""
    # TODO - verify that duplicate assignments are not supported
    # TODO - conflate the comments if duplicates are attempted
    queryset = EngineeringAssignment.objects.all()
    serializer_class = EngAssignmentSerializer
    filter_fields = ('grid_cell', 'file', 'date_assigned')
    renderer_classes = (JSONRenderer,)

    @list_route(methods=['post', ])
    def _delete(self, request):
        """Remove the specified assignment object"""
        files = request.POST['files'].split(",")
        cell_values = request.POST['grid_cells'].split(",")
        pre_assignments = len(EngineeringAssignment.objects.all())

        for x in files:
            file = EngineeringFileModel.objects.get(pk=x)
            for cell_value in cell_values:
                obj = EngineeringAssignment.objects.filter(file=file).filter(grid_cell=cell_value)
                for o in obj:
                    o.delete()

        post_assignments = len(EngineeringAssignment.objects.all())

        resp = {}
        num_removed = pre_assignments - post_assignments

        if num_removed > 0:
            resp['status'] = "{} of {} assignments were removed".format(
                    num_removed, pre_assignments)
        else:
            resp['status'] = False
        return Response(resp)

    @list_route(methods=['post', ])
    def _create(self, request):
        """Create assignment from the list of files and the grid cell on the Post request"""
        file_pks = request.POST['files'].split(",")
        cell_values = request.POST['grid_cells'].split(",")

        pre_assignments = len(EngineeringAssignment.objects.all())

        new_assignments = list()

        for x in file_pks:
            file = EngineeringFileModel.objects.get(pk=x)
            for cell_value in cell_values:
                try:
                    grid = GridCell.objects.get(pk=cell_value)
                    kwargs = dict()
                    kwargs['file'] = file
                    kwargs['grid_cell'] = grid
                    base_name = EngineeringFileModel.objects.get(pk=x).base_name
                    kwargs['base_name'] = base_name
                    # the grid_cell and file fields are defined as unique together in the model
                    # Exception is thrown if the Unique Together fails
                    assign = EngineeringAssignment.objects.create(**kwargs)
                    new_assignments.append(assign.pk)
                except Exception as e:
                    logging.error(e)

        post_assignments = len(EngineeringAssignment.objects.all())
        if post_assignments > pre_assignments:
            assignments = EngineeringAssignment.objects.filter(pk__in=new_assignments)
            serializer = EngAssignmentSerializer(assignments, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({"status": "Assignments were not created!"})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngViewSet(viewsets.ModelViewSet):
    queryset = EngineeringFileModel.objects.all()
    serializer_class = EngSerializer
    filter_fields = ('project_title', 'sheet_name', 'airport')
    renderer_classes = (JSONRenderer,)

    @detail_route()
    def _grids(self, request, pk=None):
        """grid cells that the file as been assigned to"""
        if request.user.is_authenticated():
            queryset = EngineeringAssignment.objects.filter(file_id__exact=str(pk))
            grid_cells = [x.grid_cell for x in queryset]
            serializer = GridSerializer(grid_cells, many=True)
            return Response(serializer.data)
        else:
            return redirect(reverse('home:login'))


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PagedEngViewSet(PagedFileViewSet):
    queryset = EngineeringFileModel.objects.all()
    serializer_class = EngSerializer
    filter_fields = ('project_title', 'sheet_name', 'airport')

    @detail_route(methods=['get', ])
    def _view(self, request, pk=None):
        """Return a pdf or image as an http response"""
        if request.user.is_authenticated():
            """Returns either an image http response or a pdf http response"""
            file_obj = EngineeringFileModel.objects.filter(id__exact=str(pk))
            base_name = file_obj[0].base_name
            extension = base_name.split(".")[-1].lower()
            file_path = file_obj[0].file_path.replace("\\", '/')
            response = create_response_object(file_path, extension)
            return response
        else:
            return redirect(reverse('home:login'))

    @list_route(methods=['get', ])
    def _build(self, request):
        """Traverse through the list of paths in the buildDocStore.py file and build the sqlite db"""
        if request.user.is_authenticated():
            # TODO streaming http response to update a chart showing statistics of created file object types
            trainer.stop_monitors()
            tool = buildDocStore.FileStoreBuilder()
            tool.build_store()
            trainer.start_monitors()
            return Response("build successful")

        else:
            return redirect(reverse('home:login'))

    @detail_route(methods=['get', ])
    def _delete(self, request, pk=None):
        """Remove the specified file and its assignments from the sqlite database"""
        if request.user.is_authenticated():
            _file = EngineeringFileModel.objects.filter(id__exact=str(pk))[0]
            path = _file.file_path
            if os.path.exists(path):
                _file.delete()
                return Response("{} has been deleted".format(path))
        else:
            return redirect(reverse('home:login'))

    @detail_route(methods=['get', ])
    def _grids(self, request, pk=None):
        """Grid cells that the file has been assigned to"""
        if request.user.is_authenticated():
            queryset = EngineeringAssignment.objects.filter(file_id__exact=str(pk))
            grid_cells = [x.grid_cell for x in queryset]
            serializer = GridSerializer(grid_cells, many=True)
            return Response(serializer.data)
        else:
            return redirect(reverse('home:login'))

    @list_route(methods=['get', ])
    def _clean(self, request):
        """Remove files that are not included in the TOP_DIRs; or are non-existent"""
        if request.user.is_authenticated():
            # TODO create return from File Store Builder showing stats from the removed files
            trainer.stop_monitors()
            tool = buildDocStore.FileStoreBuilder()
            tool.clean_store()
            trainer.start_monitors()
            return Response("The Store has been cleaned")
        else:
            return redirect(reverse('home:login'))


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngIOViewSet(viewsets.ViewSet):
    """This view is used to download files"""
    # TODO group download file requests into a zip file
    queryset = EngineeringFileModel.objects.all()

    @detail_route()
    def _download(self, request, pk=None):
        """download a file as attachment"""
        if request.user.is_authenticated():
            file_obj = EngineeringFileModel.objects.filter(id__exact=str(pk))
            file_path = file_obj[0].file_path
            mime_type = file_obj[0].mime
            base_name = file_obj[0].base_name
            # filename_header = base_name.encode('utf_8')
            # response is the file binary / the request is made from an dojo anchor html element with
            # the file download option enabled
            fp = File(open(file_path, 'rb'))
            resp = HttpResponse(fp.read(), content_type=mime_type)
            resp['Content-Disposition'] = "attachment; filename= '{}'".format(base_name)

            # create entry in the analytics records table
            data = {
                "method": "print",
                "app_name": __name__
            }
            serial = RecordSerializer(data=data)
            if serial.is_valid():
                serial.save()
            else:
                logger.error("failed to enter record entry {}".format(data))
            return response
        else:
            return redirect(reverse('home:login'))

    @list_route(methods=['post'])
    def _upload(self, request):
        """TODO - upload files"""
        if request.user.is_authenticated():
            return
        else:
            return redirect(reverse('home:login'))


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserViewer(GenericAPIView):
    """View that renders the main homepage or an app depending on the template"""
    renderer_classes = (TemplateHTMLRenderer,)
    permission_classes = (AllowAny,)
    pagination_class = LargeResultsSetPagination
    template = ""
    app_name = ""

    server_url = settings.LDAP_URL

    f_types = FileTypes()
    choices = f_types.FILE_TYPE_CHOICES

    file_types = f_types.FILE_VIEWER_TYPES
    image_types = f_types.IMAGE_VIEWER_TYPES
    table_types = f_types.TABLE_VIEWER_TYPES
    gis_types = f_types.GIS_VIEWER_TYPES

    document_types = f_types.DOC_VIEWER_TYPES

    sheet_types = f_types.engineering_sheet_types
    vendors = f_types.vendor_choices
    disciplines = f_types.engineering_discipline_choices
    airports = f_types.airport_choices
    funding_types = f_types.funding_choices

    def get(self, request, format=None):

        final_groups = authorize_user(request, self.template)

        app_name = self.app_name.strip('/')

        resp = Response(template_name=self.template)
        resp['Cache-Control'] = 'no-cache'

        # add the engineering file objects to the context
        efiles = EngineeringFileModel.objects.all()
        assignments = EngineeringAssignment.objects.all()

        base_names = set([x.base_name for x in efiles])
        sheet_titles = set([x.sheet_title for x in efiles])
        project_titles = set([x.project_title for x in efiles])
        project_descriptions = set([x.project_description for x in efiles])
        sheet_descriptions = set([x.sheet_description for x in efiles])
        file_paths = [x.file_path for x in efiles]
        grant_numbers = set([x.grant_number for x in efiles])

        chkd_f_types = [x[0] for x in self.file_types]
        chkd_i_types = [x[0] for x in self.image_types]
        chkd_t_types = [x[0] for x in self.table_types]
        chkd_d_types = [x[0] for x in self.document_types]
        chkd_gis_types = [x[0] for x in self.gis_types]

        form = FilterForm(init_base_name="", init_sheet_title="", init_sheet_types=["all"], init_project_title="",
                          init_project_desc="", init_after_date="", init_before_date="",
                          init_sheet_description="", init_vendors="", init_disciplines=['all'],
                          init_airports="rno", init_funding_types=['all'], init_file_path="", init_grant_number="",
                          chkd_f_types=chkd_f_types, chkd_i_types=chkd_i_types,
                          chkd_t_types=chkd_t_types, chkd_d_types=chkd_d_types, chkd_gis_types=chkd_gis_types,
                          init_grid_cells="", file_types=self.file_types, image_types=self.image_types, table_types=self.table_types,
                          document_types=self.document_types, gis_types=self.gis_types, sheet_types=self.sheet_types,
                          vendors=self.vendors, disciplines=self.disciplines, airports=self.airports,
                          funding_types=self.funding_types)

        resp.data = {
                     "sheet_titles": sheet_titles,
                     "project_titles": project_titles,
                     "project_descriptions": project_descriptions,
                     "sheet_descriptions": sheet_descriptions,
                     "file_paths": file_paths,
                     "grant_numbers": grant_numbers,
                     "efiles": efiles,
                     "assigns": assignments,
                     "server_url": self.server_url,
                     "groups": final_groups,
                     "app_name": app_name,
                     "form": form
                     }
        return resp

    def post(self, request, format=None):
        final_groups = authorize_user(request, self.template)
        app_name = self.app_name.strip('/')

        data = request.data
        logger.info(data)
        resp = Response(template_name=self.template)
        resp['Cache-Control'] = 'no-cache'

        base_name = data["base_name"]
        sheet_title = data["sheet_title"]
        project_title = data["project_title"]
        project_description = data["project_description"]
        after_date = data["after_date"]
        before_date = data["before_date"]
        sheet_description = data["sheet_description"]
        airport = data["airport"]
        file_path = data["file_path"]
        grant_number = data["grant_number"]
        # grid cells are in a comma delimated string
        grid_cells = data["grid_cells"]

        funding_types = data.getlist('funding_type')
        sheet_types = data.getlist('sheet_type')
        vendors = data.getlist('vendor')
        disciplines = data.getlist("discipline")
        file_types = data.getlist('file_type')
        image_types = data.getlist('image_type')
        table_types = data.getlist('table_type')
        document_types = data.getlist('document_type')
        gis_types = data.getlist('gis_type')

        # build the querysets that refine the final efile list
        if base_name:
            efiles = EngineeringFileModel.objects.filter(base_name__icontains=base_name)
        else:
            efiles = EngineeringFileModel.objects.all()

        if sheet_title:
            efiles = EngineeringFileModel.objects.filter(sheet_title__icontains=sheet_title)
        if project_title:
            efiles = efiles.filter(project_title__icontains=project_title)
        if project_description:
            efiles = efiles.filter(project_description__icontains=project_description)
        if after_date:
            efiles = efiles.filter(after_date__gte=after_date)
        if before_date:
            efiles = efiles.filter(before_date__lte=before_date)
        if sheet_description:
            efiles = efiles.filter(sheet_description__icontains=sheet_description)
        # not all files are attributed yet so only filter for rst if requested
        if airport != 'rno':
            efiles = efiles.filter(airport=airport)
        if file_path:
            efiles = efiles.filter(file_path__icontains=file_path)
        if grant_number:
            gnums = [x.strip() for x in grant_number.split()]
            efiles = efiles.filter(grant_number__in=gnums)
        if grid_cells:
            gcells = [x.strip() for x in grid_cells]
            efiles = efiles.filter(engineeringassignment__grid_cell_id__in=gcells)
        if funding_types and funding_types != ['all']:
            efiles = efiles.filter(funding_type__in=funding_types)
        if sheet_types and sheet_types != ['all']:
            efiles = efiles.filter(sheet_type__in=sheet_types)
        if vendors and vendors != ['all']:
            efiles = efiles.filter(vendor__in=vendors)
        if disciplines and disciplines != ['all']:
            efiles = efiles.filter(discipline__in=disciplines)

        # Look up dict to use until bug is fixed with variable names/keys
        # lookup = {}
        # for x in [self.file_types, image_types, table_types, gis_types]:
        #     lookup[]
        # Pre file type filters
        base_types = file_types[:]
        base_types.extend(image_types)
        base_types.extend(table_types)
        base_types.extend(gis_types)

        if len(base_types) != len(self.choices):
            # efiles = efiles.filter(file_type__in=base_types)
            efiles = efiles.filter(file_type__in=base_types)
        # only filter by doc type if they are not all selected
        if len(document_types) != len(self.document_types):
            efiles = efiles.filter(document_type__in=document_types)

        # after all of the files have been filtered from the input, query the assignments
        assignments = EngineeringAssignment.objects.filter(file__in=efiles)

        base_names = set([x.base_name for x in efiles])
        sheet_titles = set([x.sheet_title for x in efiles])
        project_titles = set([x.project_title for x in efiles])
        project_descriptions = set([x.project_description for x in efiles])
        sheet_descriptions = set([x.sheet_description for x in efiles])
        file_paths = [x.file_path for x in efiles]
        grant_numbers = set([x.grant_number for x in efiles])

        form = FilterForm(init_base_name=base_name, init_sheet_title=sheet_title, init_sheet_types=sheet_types,
                          init_project_title=project_title, init_project_desc=project_description,
                          init_after_date=after_date, init_before_date=before_date,
                          init_sheet_description=sheet_description, init_vendors=vendors, init_disciplines=disciplines,
                          init_airports=airport, init_funding_types=funding_types, init_file_path=file_path,
                          init_grant_number=grant_number, chkd_f_types=file_types, chkd_i_types=image_types,
                          chkd_t_types=table_types, chkd_d_types=document_types, chkd_gis_types=gis_types,
                          init_grid_cells=grid_cells, file_types=self.file_types, image_types=self.image_types,
                          table_types=self.table_types, document_types=self.document_types,
                          sheet_types=self.sheet_types, gis_types=self.gis_types, vendors=self.vendors,
                          disciplines=self.disciplines, airports=self.airports,
                          funding_types=self.funding_types)

        resp.data = {
            "base_names": base_names,
            "sheet_titles": sheet_titles,
            "project_titles": project_titles,
            "project_descriptions": project_descriptions,
            "sheet_descriptions": sheet_descriptions,
            "file_paths": file_paths,
            "grant_numbers": grant_numbers,
            "efiles": efiles,
            "assigns": assignments,
            "server_url": self.server_url,
            "groups": final_groups,
            "app_name": app_name,
            "form": form
        }
        return resp
