from __future__ import unicode_literals
from analytics.serializers import RecordSerializer
from rest_framework.decorators import api_view, renderer_classes, authentication_classes
from rest_framework_jsonp.renderers import JSONPRenderer
import logging
import os
import sys
import subprocess
from subprocess import PIPE
from subprocess import TimeoutExpired
import arcgis
from arcgis import mapping

from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import ensure_csrf_cookie
from io import BytesIO
from rest_framework.response import Response
from django.http import HttpResponse
from django.core.files import File
from datetime import datetime
import mimetypes
import json
import shlex
import threading
from django.conf import settings
MEDIA_ROOT = settings.MEDIA_ROOT

environ = "rtaa_testing"
username = "gissetup"


def system_paths(environ):
    arcmap_path = {
        "work": r"C:\Python27\ArcGIS10.4\python.exe",
        "rtaa_testing": r"C:\Python27\ArcGIS10.5\python.exe"
    }
    arcmap_path = arcmap_path[environ]

    mxd_script = {
        "work": r"C:\GitHub\rtaa_gis\rtaa_gis\printTool\utils\ConvertWebMaptoMXD.py",
        "rtaa_testing": r"C:\GitHub\rtaa_gis_django\rtaa_gis\printTool\utils\ConvertWebMaptoMXD.py"
    }
    mxd_script = mxd_script[environ]

    media_dir = {
        "work": "C:/GitHub/rtaa_gis/rtaa_gis/media",
        "staging": r"C:/GitHub/rtaa_gis_django/rtaa_gis/rtaa_gis/media",
        "production": "C:/inetpub/django_prod/rtaa_gis/rtaa_gis/media",
        "rtaa_testing": r"C:\inetpub\rtaa_gis_django_testing\rtaa_gis\media"
    }
    media_dir = media_dir[environ]

    gdb_path = {
        "work": r"C:\ESRI_WORK_FOLDER\rtaa\MasterGDB\MasterGDB_05_25_16\MasterGDB_05_25_16.gdb",
        "staging": r"C:\inetpub\rtaa_gis_data\MasterGDB_05_25_16\MasterGDB_05_25_16.gdb",
        "production": r"C:\inetpub\rtaa_gis_data\MasterGDB_05_25_16\MasterGDB_05_25_16.gdb",
        "rtaa_testing": r"D:\ConnectionFiles\OSAuth@RTAA_MasterGDB.sde"
    }
    gdb_path = gdb_path[environ]

    default_project = {
        "work": r"C:\Users\rhughes\Documents\ArcGIS\Projects\RTAA_Printing_Publishing\RTAA_Printing_Publishing.aprx",
        "staging": r"C:\inetpub\rtaa_gis_data\RTAA_Printing_Publishing\RTAA_Printing_Publishing.aprx",
        "production": r"C:\inetpub\rtaa_gis_data\RTAA_Printing_Publishing\RTAA_Printing_Publishing.aprx",
        "rtaa_testing": r"D:\ArcPro\RTAA_Publishing\RTAA_Publishing.aprx"
    }
    default_project = default_project[environ]

    layer_dir = {
        "work": r"C:\ESRI_WORK_FOLDER\rtaa\layers",
        "staging": r"C:\inetpub\rtaa_gis_data\RTAA_Printing_Publishing\FeatureLayers",
        "production": r"C:\inetpub\rtaa_gis_data\RTAA_Printing_Publishing\FeatureLayers",
        "rtaa_testing": r"D:\ArcPro\RTAA_Publishing\FeatureLayers"
    }
    layer_dir = layer_dir[environ]

    return {
        "arcmap_path": arcmap_path,
        "mxd_script": mxd_script,
        "gdb_path": gdb_path,
        "layer_dir": layer_dir,
        "default_project": default_project,
        "media_dir": media_dir
    }


def get_username(request):
    try:
        username = request.META['REMOTE_USER'].split("\\")[-1]
    except KeyError:
        username = request.user.username
    if not len(username):
        username = "Anonymous"
    return username


def insert_token(webmap, token):
    op_layers = webmap["operationalLayers"]
    new_ops = list()

    for x in op_layers:
        keys = x.keys()
        if "url" in keys:
            service_url = x["url"]
            if "https://services.arcgisonline.com" in service_url:
                new_ops.append(x)
            else:
                x['token'] = token
                new_ops.append(x)
        else:
            new_ops.append(x)

    webmap["operationalLayers"] = new_ops
    return webmap


def name_file(out_folder, file):
    file_name = os.path.basename(file)
    logger.info("Downloaded file named {}".format(file_name))
    os.chdir(out_folder)
    extension = file.split(".")[-1]
    base_name = "GISViewer_export"
    full_name = "{}.{}".format(base_name, extension)
    if os.path.exists(full_name):
        v = 1
        full_name = "{}_{}.{}".format(base_name, v, extension)
        if os.path.exists(full_name):
            i = False
            while not i:
                v += 1
                full_name = "{}_{}.{}".format(base_name, v, extension)
                if not os.path.exists(full_name):
                    i = True

    try:
        os.rename(file_name, full_name)
    except OSError:
        logger.error("printed map unable to be saved with correct filename")

    return full_name


logger = logging.getLogger(__package__)


# Create your views here.
@api_view(['POST'])
# @renderer_classes((JSONPRenderer,))
@authentication_classes((AllowAny,))
@ensure_csrf_cookie
def print_agol(request, format=None):
    username = get_username(request)
    out_folder = os.path.join(MEDIA_ROOT, 'users/{}/prints'.format(username))

    gis = arcgis.gis.GIS(url="https://rtaa.maps.arcgis.com",
                         username="data_owner",
                         password="GIS@RTAA123!")

    token = gis._con._token
    # logger.info(token)
    data = request.POST

    webmap = data['Web_Map_as_JSON']
    map_obj = json.loads(webmap)
    map_obj = insert_token(map_obj, token)
    map_json = json.dumps(map_obj)
    # logger.info(map_json)

    format = data['Format']
    layout_template = data['Layout_Template']
    # layout_template = "A3 Landscape"
    data = mapping.export_map(web_map_as_json=map_json, format=format,
                       layout_template=layout_template,
                       gis=gis)

    file = data.download(out_folder)
    full_name = name_file(out_folder=out_folder, file=file)

    response = Response()

    host = request.META["HTTP_HOST"]
    media_url = settings.MEDIA_URL.lstrip("/")
    media_url = media_url.rstrip("/")

    if host == "127.0.0.1:8080":
        protocol = "http"
    else:
        protocol = "https"

    url = "{}://{}/{}/users/{}/prints/{}".format(protocol, host, media_url, username, full_name)

    response.data = {
        "messages": [],
        "results": [{
            "value": {
                "url": url
            },
            "paramName": "Output_File",
            "dataType": "GPDataFile"
        }]
    }

    data = {
        "method": "print",
        "app_name": "Print"
    }
    serial = RecordSerializer(data=data, context={'request': request})
    if serial.is_valid():
        serial.save()
    else:
        logger.error("Unable to save count :: {}".format(data))
    return response


@api_view(['POST'])
# @renderer_classes((JSONPRenderer,))
@authentication_classes((AllowAny,))
@ensure_csrf_cookie
def print_mxd(request, format=None):
    username = get_username(request)
    out_folder = os.path.join(MEDIA_ROOT, 'users/{}/prints'.format(username))

    v = system_paths(environ)
    arcmap_path = v["arcmap_path"]
    mxd_script = v["mxd_script"]

    gis = arcgis.gis.GIS(url="https://rtaa.maps.arcgis.com",
                         username="data_owner",
                         password="GIS@RTAA123!")

    token = gis._con._token
    data = request.POST
    webmap = data['Web_Map_as_JSON']

    map_obj = json.loads(webmap)
    map_obj = insert_token(map_obj, token)
    map_json = json.dumps(map_obj)
    temp_file = os.path.join(out_folder, "webmap.json")
    if os.path.exists(temp_file):
        os.remove(temp_file)
    f = open(temp_file, 'w')
    f.write(map_json)
    f.close()

    format = data['Format']
    layout_template = data['Layout_Template']

    args = [arcmap_path, mxd_script, '-media_dir', MEDIA_ROOT, '-username', username, '-layout', layout_template, '-format', format]
    proc = subprocess.Popen(args, executable=arcmap_path, stderr=PIPE, stdout=PIPE)
    out, err = proc.communicate()

    full_name = name_file(out_folder=out_folder, file=out.decode())
    response = Response()
    # This format must be identical to the DataFile object returned by the esri print examples
    host = request.META["HTTP_HOST"]

    if host == "127.0.0.1:8080":
        protocol = "http"
    else:
        protocol = "https"
    media_url = settings.MEDIA_URL.lstrip("/")
    media_url = media_url.rstrip("/")

    url = "{}://{}/{}/users/{}/prints/{}".format(protocol, host, media_url, username, full_name)
    logger.info(url)
    response.data = {
        "messages": [],
        "results": [{
            "value": {
                "url": url
            },
            "paramName": "Output_File",
            "dataType": "GPDataFile"
        }]
    }
    return response


@api_view(['POST'])
# @renderer_classes((JSONPRenderer,))
@authentication_classes((AllowAny,))
@ensure_csrf_cookie
def print_arcmap(request, format=None):
    username = get_username(request)
    out_folder = os.path.join(MEDIA_ROOT, 'users/{}/prints'.format(username))

    v = system_paths(environ)
    arcmap_path = v["arcmap_path"]
    mxd_script = v["mxd_script"]

    data = request.POST
    webmap = data['Web_Map_as_JSON']

    map_obj = json.loads(webmap)


    format = data['Format']
    layout_template = data['Layout_Template']

    args = [arcmap_path, mxd_script, '-media_dir', MEDIA_ROOT, '-username', username, '-layout', layout_template,
            '-format', format]
    proc = subprocess.Popen(args, executable=arcmap_path, stderr=PIPE, stdout=PIPE)
    out, err = proc.communicate()

    full_name = name_file(out_folder=out_folder, file=out.decode())
    response = Response()
    # This format must be identical to the DataFile object returned by the esri print examples
    host = request.META["HTTP_HOST"]

    if host == "127.0.0.1:8080":
        protocol = "http"
    else:
        protocol = "https"
    media_url = settings.MEDIA_URL.lstrip("/")
    media_url = media_url.rstrip("/")

    url = "{}://{}/{}/users/{}/prints/{}".format(protocol, host, media_url, username, full_name)
    logger.info(url)
    response.data = {
        "messages": [],
        "results": [{
            "value": {
                "url": url
            },
            "paramName": "Output_File",
            "dataType": "GPDataFile"
        }]
    }
    return response


@api_view(['POST', 'GET'])
@authentication_classes((AllowAny,))
@ensure_csrf_cookie
def getPrintList(request, format=None):
    username = get_username(request)
    print_dir = os.path.join(MEDIA_ROOT, "users/{}/prints".format(username))
    logger.info(print_dir)

    response = Response()
    response.data = list()
    if os.path.exists(print_dir):
        files = os.listdir(print_dir)
        selection = []
        for x in [".png", ".pdf", ".jpg", ".gif", ".eps", ".svg", ".svgz"]:
            selection.extend([f for f in files if f.endswith(x)])

        response['Cache-Control'] = 'no-cache'
        host = request.META["HTTP_HOST"]
        if host == "127.0.0.1:8080":
            protocol = "http"
        else:
            protocol = "https"
        media_url = settings.MEDIA_URL.lstrip("/")
        media_url = media_url.rstrip("/")

        for out_file in selection:
            url = "{}://{}/{}/users/{}/prints/{}".format(protocol, host, media_url, username, out_file)
            response.data.append({"url": url})
    else:
        response.data.append("Error, print directory not found")

    return response


@api_view(['POST'])
@authentication_classes((AllowAny,))
@ensure_csrf_cookie
def delete_file(request, format=None):
    username = get_username(request)
    data = request.POST
    file_name = data["filename"].replace("\n", "")
    outfolder = os.path.join(MEDIA_ROOT, "users/{}/prints".format(username))
    response = Response()

    if os.path.exists(outfolder):
        os.chdir(outfolder)
        if os.path.exists(file_name):
            os.remove(file_name)
            data = "Temp File {} Deleted from Server".format(file_name)
        else:
            data = "File not found in user's print folder"
    else:
        data = "Failed to located user's media folder"
    response.data = data
    return response