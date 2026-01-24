from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailTemplateViewSet

router = DefaultRouter()
router.register(r'templates', EmailTemplateViewSet, basename='template')

app_name = 'templates'

urlpatterns = [
    path('', include(router.urls)),
]