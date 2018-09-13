import ldap3
import django
import sys
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import os
import pprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rtaa_gis.settings'
django.setup()
from django.contrib.auth.models import Group


class LDAPQuery:
    """
    Instantiate this class with a remote user name and
        perform queries on Active Directory or LDAP
    """
    def __init__(self, username, ldap_url):
        self.username = username.split("\\")[-1]
        self.ldap_url = ldap_url
        self.target_groups = [
            '_RTAA Planning and Engineering',
            '_RTAA Airport Economic Development',
            '_RTAA Finance & Administration',
            '_RTAA GIS',
            'GIS_Airspace_Group',
            'GIS_LPM_Admin',
            'Arora'
        ]
        for group in self.target_groups:
            try:
                Group.objects.get(name=group)
            except Group.DoesNotExist:
                Group.objects.create(name=group)
        # self.server = Server(ldap_url, port=636, get_info=ALL, use_ssl=False)
        self.server = Server(ldap_url, get_info=ALL)

    def get_user_info(self):
        """in this function we are returning the user's groups, first name, last name, and their email"""
        user_info = {
            "firstName": "",
            "lastName": "",
            "email": "",
            "groups": []
        }

        try:
            user = None
            password = None
            search_base = None
            if self.ldap_url == "renoairport.net":
                user = "RENOAIRPORT\\AroraTeam"
                password = "@R0r@G1$"
                search_base = "dc=renoairport, dc=net",
            elif self.ldap_url == "gisapps.aroraengineers.com":
                user = "GISAPPS\\gissetup"
                password = "AroraGIS123:)"
                search_base = "dc=gisapps, dc=aroraengineers, dc=com"

            conn = Connection(self.server, user=user, password=password, authentication=NTLM,
                              auto_bind=False)
            # conn = Connection(self.server, auto_bind=True)
            conn.bind()
            # conn.start_tls()
            total_entries = 0
            try:
                conn.search(
                    search_base=search_base,
                    search_filter="(&(objectclass=user)(sAMAccountName={}))".format(self.username),
                    search_scope=SUBTREE,
                    attributes=ldap3.ALL_ATTRIBUTES,
                )

            except Exception as e:
                print("Exception arguments: {}".format(e.args))

            total_entries += len(conn.response)
            print(conn.response)
            for entry in conn.response:
                try:
                    print("dn: [{}], attributes: {}".format(entry['dn'], entry['attributes']))
                    groups = entry['attributes']['memberOf']
                    email = entry['attributes']['userPrincipalName']
                    full_name = entry['attributes']['name'].split(",")
                    first_name = full_name[-1]
                    last_name = full_name[0]

                    for x in groups:
                        group = x.split(',')[0].split('=')[-1]
                        if group in self.target_groups:
                            user_info["groups"].append(group)
                    user_info["email"] = email
                    user_info["firstName"] = first_name
                    user_info["lastName"] = last_name

                except KeyError:
                    pass

            # print('Total entries retrieved', total_entries)
            try:
                conn.unbind()
            except Exception as e:
                print("Exception arguments: {}".format(e.args))

        except Exception as e:
            print(e)

        pprint.pprint(user_info)
        return user_info


if __name__ == "__main__":
    query = LDAPQuery("RENOAIRPORT\\AroraTeam", "renoairport.net")
    x = query.get_user_info()
    print(x)

