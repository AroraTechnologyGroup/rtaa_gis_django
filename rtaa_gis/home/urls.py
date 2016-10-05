from django.conf.urls import url
from django.contrib.auth.views import logout, login, password_change
from .views import HomePage
from rest_framework.authtoken import views


app_name = 'home'
urlpatterns = [
    url(r'^$', HomePage.as_view(), name='index'),
    url(r'^login/$', login, {'extra_context': {'next': '/#home'}}, name='login'),
    url(r'^logout/$', logout, {'next_page': 'home:login'}, name='logout'),
    url(r'^dojo-login/$', views.obtain_auth_token, name='dojo-login'),
    # url(r'^password_change/$', password_change, {'post_change_redirect': 'home:login'}, name='password_change')
]



