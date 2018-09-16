from django.urls import path
from django.contrib.auth.views import logout, login, password_change
from .views import HomePage, user_auth, schema_view
from rest_framework.authtoken import views as rest_framework_views

app_name = 'home'
urlpatterns = [
    path('', HomePage.as_view(), name='index'),
    path('docs', schema_view, name="docs"),
    path('user_info', user_auth, name="user_info"),
    path('login', login, {'extra_context': {'next': '/#home'}}, name='login'),
    path('logout', logout, {'next_page': 'home:login'}, name='logout'),
    path('get_auth_token', rest_framework_views.obtain_auth_token, name='get_auth_token'),

    # These urls for web mapping applications are also specified in the application_cards.json file, loaded
    # with the static files for the home app, as the value for the 'path' key.
    # The app_name corresponds to the application on IIS that gets loaded in the iframe
    path('viewer', HomePage.as_view(template='home/AppLoader.html', app_name='gisviewer'), name='viewer'),
    path('airspace', HomePage.as_view(template='home/AppLoader.html', app_name='airspace_restricted'),
        name='airspace'),
    path('leaseProperty', HomePage.as_view(template='home/AppLoader.html', app_name='rtaa_lpm'),
        name='lpm'),
    path('signageMarking', HomePage.as_view(template='home/AppLoader.html', app_name='Signs'),
        name='signage'),
    path('mobile', HomePage.as_view(template='home/AppLoader.html', app_name='mobile'), name='mobile'),
    # url(r'^password_change/$', password_change, {'post_change_redirect': 'home:login'}, name='password_change')
]
