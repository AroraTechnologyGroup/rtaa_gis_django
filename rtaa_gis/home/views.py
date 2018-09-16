from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.template.response import TemplateResponse
from rest_framework.response import Response
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.permissions import AllowAny
from .utils.ldap_tool import LDAPQuery
from .utils.app_config import WebConfig
from .utils.agol_user import clear_old_users
from home.models import App, ProxyUser
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import logging
from datetime import datetime
from rest_framework_jsonp.renderers import JSONRenderer
import os
from django.conf import settings
from django.views.decorators.cache import never_cache
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer


logger = logging.getLogger(__package__)

schema_view = get_schema_view(title='RTAA API', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer])


def process_configs():
    # These are the folders that the apps are deployed into on IIS
    if settings.LDAP_URL == "renoairport.net":
        viewer_dir = "RTAA Viewer"
        lpm_dir = "RTAA Lease and Property Management"
        airspace_dir = "airspace"
        signage_dir = "signs"

    elif settings.LDAP_URL == "gisapps.aroraengineers.com":
        viewer_dir = "RTAA Viewer"
        lpm_dir = "RTAA Lease and Property Management"
        airspace_dir = "airspace"
        signage_dir = "signs"

    # Here these objects represent apps hosted on django framework, not IIS.
    # the groups set the read-only level permissions
    edoc = {
        "name": "e-doc",
        "path": None,
        "groups": ['_RTAA Planning and Engineering', '_RTAA GIS', "Arora"]
    }
    if settings.DEBUG:
        edoc["groups"].append("All Users")

    mobile = {
        "name": "mobile",
        "path": None,
        "groups": ["All Users"]
    }

    web_config = WebConfig(viewer_dir=viewer_dir, lpm_dir=lpm_dir, airspace_dir=airspace_dir, signage_dir=signage_dir)
    web_config.load(edoc)
    web_config.load(mobile)

    # create a group for each in every app's group authorization list
    cur_groups = [g.name for g in Group.objects.all()]
    for group in web_config.groups:
        if group not in cur_groups:
            try:
                Group.objects.create(name=group)
            except Exception as e:
                logger.error(e)

    # remove groups from the database if they were not found in the config file's groups
    cur_groups = Group.objects.all()
    target_groups = web_config.groups[:]
    for x in cur_groups:
        if x.name not in target_groups:
            try:
                x.delete()
            except Exception as e:
                logger.error(e)

    # remove apps that were not found in web configs or text inputs
    for x in App.objects.all():
        if x.name not in web_config.apps:
            x.delete()

    # create the app objects from the parsed configs and django apps
    all_apps = [x.name for x in App.objects.all()]
    for app in web_config.apps:
        if type(app) == dict:
            name = app["name"]
            groups = app["groups"]
            if name not in all_apps:
                # create the app object if it was not found
                try:
                    App.objects.create(name=name)
                except Exception as e:
                    logger.error(e)
            try:
                obj = App.objects.get(name=name)
                # remove groups from the app if they no longer are assigned
                existing = obj.groups.all()
                for gr in existing:
                    if gr.name not in groups:
                        try:
                            gr.delete()
                        except Exception as e:
                            logger.error(e)

                if "All Users" in groups:
                    obj.public = True
                else:
                    obj.public = False

                # load the groups onto the apps
                for group in groups:
                    try:
                        gr = Group.objects.get(name=group)
                        obj.groups.add(gr)
                    except Exception as e:
                        logger.error(e)
                obj.save()

            except Exception as e:
                logger.error(e)

    return web_config


def query_ldap(name):
    """this functions is used in the api function view and the HomePage View Class"""
    # Perform inheritance from AD
    local_name = name.split("\\")[-1]
    if settings.LDAP_URL == "renoairport.net":
        if settings.DEBUG:
            local_name = "AroraTeam"

    query = LDAPQuery(local_name, settings.LDAP_URL)
    user_info = query.get_user_info()
    ldap_groups = user_info["groups"]
    first_name = user_info["firstName"]
    last_name = user_info["lastName"]
    email = user_info["email"]

    logger.info("ldap_groups = {}".format(ldap_groups))
    logger.info("firstName = {}".format(first_name))
    logger.info("lastName = {}".format(last_name))
    logger.info("email = {}".format(email))

    user_obj = User.objects.get(username=name)
    users_groups = user_obj.groups.all()
    # remove groups from user if not in LDAP group list
    for x in users_groups:
        if x.name not in ldap_groups:
            try:
                user_obj.groups.remove(x)
            except Exception as e:
                print(e)
    # add user to group if not already a member
    for x in ldap_groups:
        if x not in [g.name for g in users_groups]:
            try:
                g = Group.objects.get(name=x)
                if g:
                    user_obj.groups.add(g)
            except Exception as e:
                print(e)

    user_obj.first_name = first_name
    user_obj.last_name = last_name
    user_obj.email = email
    user_obj.save()

    new_user_obj = User.objects.get(username=name)
    groups = [x.name for x in new_user_obj.groups.all()]
    first_name = new_user_obj.first_name
    last_name = new_user_obj.last_name
    email = new_user_obj.email

    data = {
        "user": local_name,
        "groups": groups,
        "firstName": first_name,
        "lastName": last_name,
        "email": email
    }
    return data


def get_user_info(request):
    """from the request return the domain username or the local user for testing"""
    try:
        name = request.META['REMOTE_USER']
        logger.info("Remote username = {}".format(name))
    except KeyError:
        name = request.user.username
        logger.info("non-Remote username = {}".format(name))
    # for testing, if username is '', set it to superuser from django admin
    if name == '':
        name = 'siteadmin'

    # proxy model with custom method to return list of app names
    proxy_user = ProxyUser.objects.get(username=name)
    final_apps = proxy_user.get_apps()

    user_groups = proxy_user.groups.all()
    if len(user_groups):
        # storing just the name of the group
        user_groups = [x.name for x in user_groups]
        user_groups.sort()

    return {"name": name, "final_apps": final_apps, "user_groups": user_groups}


@api_view(['GET', 'POST'])
def user_auth(request, format=None):
    """View to get the user's auth info from the framework tables"""
    info = get_user_info(request)
    name = info["name"]
    final_apps = info["final_apps"]
    user_groups = info["user_groups"]
    local_name = name.split("\\")[-1]
    user_obj = User.objects.get(username=name)

    first_name = user_obj.first_name
    last_name = user_obj.last_name
    email = user_obj.email

    user_data = {
        "username": name,
        "local_name": local_name,
        "groups": user_groups,
        "apps": final_apps,
        "firstName": first_name,
        "lastName": last_name,
        "email": email
    }
    return Response(user_data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
# @method_decorator(never_cache, name="dispatch")
class HomePage(APIView):
    """View that renders the main homepage or an app depending on the template"""
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (AllowAny,)
    template = r'home/home_body.html'
    app_name = ""

    def get(self, request, format=None):

        if not request.user.is_authenticated:
            return redirect(reverse('home:login'))

        resp = Response(template_name=self.template)
        resp['Cache-Control'] = 'no-cache'

        # read the web.config for each app and build the App model with authorization groups
        web_config = process_configs()

        # important to update the apps and auth groups from configs before users
        # run this function to inherit groups from AD
        query_ldap(request.user.username)
        user_info = get_user_info(request)

        user_groups = user_info["user_groups"]

        # return the list of apps the user can view
        final_apps = user_info["final_apps"]

        local_name = request.user.username.split("\\")[-1]
        # Create user's folder in the media root
        users_dir = os.path.join(settings.MEDIA_ROOT, 'users')
        if not os.path.exists(users_dir):
            os.mkdir(users_dir)
        user_dir = os.path.join(users_dir, local_name)
        if not os.path.exists(user_dir):
            os.mkdir(user_dir)

        server_url = settings.SERVER_URL
        app_name = self.app_name.strip('/')

        resp.data = {"server_url": server_url, "apps": final_apps, "groups": user_groups,
                     "app_name": app_name}
        return resp
