from django.conf.urls import include, url
from django.contrib.auth.views import logout, login, password_change
from .views import HomePage, GitPull
from django.urls import reverse

app_name = 'home'
urlpatterns = [
    url(r'^$', HomePage.as_view(), name='index'),
    url(r'^git-pull/$', GitPull.as_view()),
    url(r'^login/$', login, {'extra_context': {'next': '/#home'}}, name='login'),
    url(r'^logout/$', logout, {'next_page': 'home:login'}, name='logout'),
    # url(r'^password_change/$', password_change, {'post_change_redirect': 'home:login'}, name='password_change')
]



