from django.conf.urls import url
from django.contrib.auth.views import logout, login, password_change
from .views import HomePage, user_groups, clear_users

app_name = 'home'
urlpatterns = [
    url(r'^$', HomePage.as_view(), name='index'),
    url(r'^groups/$', user_groups),
    url(r'^login/$', login, {'extra_context': {'next': '/#home'}}, name='login'),
    url(r'^logout/$', logout, {'next_page': 'home:login'}, name='logout'),
    url(r'^clear/$', clear_users),
    url(r'^viewer/$', HomePage.as_view(template='home/iframeLoader.html', app_name='rtaa_viewer'), name='viewer'),
    url(r'^eDoc/$', HomePage.as_view(template='home/iframeLoader.html', app_name='eDoc'), name='eDoc'),
    url(r'^airspace/$', HomePage.as_view(template='home/iframeLoader.html', app_name='rtaa_airspace'), name='airspace'),
    url(r'^econDev/$', HomePage.as_view(template='home/iframeLoader.html', app_name='rtaa_property'), name='econDev'),
    url(r'^signageMarking/$', HomePage.as_view(template='home/iframeLoader.html', app_name='rtaa_viewer'), name='signageMarking'),
    url(r'^mobile/$', HomePage.as_view(template='home/iframeLoader.html', app_name='rtaa_viewer'), name='mobile'),
    # url(r'^password_change/$', password_change, {'post_change_redirect': 'home:login'}, name='password_change')
]



