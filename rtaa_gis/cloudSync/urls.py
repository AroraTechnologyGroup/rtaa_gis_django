from rest_framework import routers
from .views import OnlineViewSet, FLayerViewSet, GDBViewSet, FDatasetViewSet,\
    FClassViewSet, FieldViewSet, PLogViewSet, WebMapViewSet, Builder, GDBSummaryPage
from django.urls import path

app_name = 'cloudSync'
router = routers.DefaultRouter()
router.register(r'gdb', GDBViewSet)
router.register(r'dataset', FDatasetViewSet)
router.register(r'fcs', FClassViewSet)
router.register(r'field', FieldViewSet)

router.register(r'webmap', WebMapViewSet)
router.register(r'web', OnlineViewSet, base_name="web")
router.register(r'flayer', FLayerViewSet)
router.register(r'publisher', PLogViewSet)

urlpatterns = [
    path('_build', Builder.as_view(), name='builder'),
    path('summary', GDBSummaryPage.as_view(), name='summary')
]

urlpatterns += router.urls


