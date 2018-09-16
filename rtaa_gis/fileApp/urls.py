from rest_framework import routers
from . import views
from .views import UserViewer, FileUpdater
from django.urls import path

app_name = 'fileApp'

router = routers.DefaultRouter()
router.register('grids', views.EngGridViewSet)
router.register('eng-assignments', views.EngAssignmentViewSet)
router.register('eng-all-files', views.EngViewSet)
router.register('eng-io', views.EngIOViewSet)
router.register('eng-files', views.PagedEngViewSet)


urlpatterns = [
    path('eDocViewer', UserViewer.as_view(template='fileApp/eDocUserView.html', app_name='eDoc Viewer'), name='e-doc'),
    path('file-update', FileUpdater.as_view(), name='file-updater')
]

urlpatterns += router.urls
