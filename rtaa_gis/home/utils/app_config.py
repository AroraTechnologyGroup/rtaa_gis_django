import django
import sys
import os
import logging

import xml.etree.ElementTree as ET
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rtaa_gis.settings'
django.setup()
from django.conf import settings

logger = logging.getLogger(__name__)

root_path = settings.IIS_APP_ROOT
if not os.path.exists(root_path) and settings.DEBUG:
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_configs")

if settings.LDAP_URL == "renoairport.com":
    viewer_dir = "RTAA Viewer"
    lpm_dir = "RTAA Lease and Property Management"
    airspace_dir = "airspace"
    signage_dir = "signs"

elif settings.LDAP_URL == "gisapps.aroraengineers.com":
    viewer_dir = "RTAA Viewer"
    lpm_dir = "RTAA Lease and Property Management"
    airspace_dir = "airspace"
    signage_dir = "signs"


class WebConfig:
    """
    A base class to store apps urls.  Inherit this class and populate for the server being used
    """

    def __init__(self, viewer_dir, lpm_dir, airspace_dir, signage_dir):
        viewer = {
            "name": "viewer",
            "path": os.path.join(root_path, r"{}\web.config".format(viewer_dir)),
            "groups": []
        }
        lpm = {
            "name": "lpm",
            "path": os.path.join(root_path, r"{}\web.config".format(lpm_dir)),
            "groups": []
        }
        airspace = {
            "name": "airspace",
            "path": os.path.join(root_path, r"{}\web.config".format(airspace_dir)),
            "groups": []
        }
        signage = {
            "name": "signage",
            "path": os.path.join(root_path, r"{}\web.config".format(signage_dir)),
            "groups": []
        }
        self.apps = [viewer, lpm, airspace, signage]
        self.groups = self.collect_groups()

    def load(self, obj):
        """ allows for loading apps and groups that don't are django hosted without a web.config"""
        self.apps.append(obj)
        self.groups = self.collect_groups()

    def collect_groups(self):
        groups = []
        for x in self.apps:
            """only run if a web.config path is defined"""
            if x["path"]:
                if os.path.exists(x["path"]):
                    obj = self.parseAppConfig(x)
                    gr = obj["groups"]
                    for g in gr:
                        if g not in groups:
                            groups.append(g)
                else:
                    logger.error("{} does not exist".format(x["path"]))
            else:
                for group in x["groups"]:
                    if group not in groups:
                        groups.append(group)
        groups.sort()
        return groups

    @staticmethod
    def parseAppConfig(input):
        """This will append the groups to each app by parsing the web.config file"""
        tree = ET.parse(input["path"])
        root = tree.getroot()
        for x in root.iter("authorization"):
            adds = x.findall("add")
            for entry in adds:
                atts = entry.attrib
                if atts["accessType"] == "Allow":
                    try:
                        if "users" in atts:
                            target_users = atts["users"]
                            if "*" == target_users:
                                # Add 'All Users' as a group for the app in the framework
                                if "All Users" not in input["groups"]:
                                    input["groups"].append("All Users")

                        target_roles = atts["roles"]
                        roles_list = [x.strip() for x in target_roles.split(",")]
                        for role in roles_list:
                            if role not in input["groups"]:
                                input["groups"].append(role)
                    except KeyError:
                        # the viewer does not have roles defined so it is safe to ignore
                        pass
        groups = input["groups"]
        gr = list(set(groups))
        input["groups"] = gr
        return input


if __name__ == "__main__":

    obj = WebConfig(viewer_dir=viewer_dir,
                    lpm_dir=lpm_dir,
                    airspace_dir=airspace_dir,
                    signage_dir=signage_dir)
    print(obj.collect_groups())
