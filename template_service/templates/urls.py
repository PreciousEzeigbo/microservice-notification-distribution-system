from django.urls import path
from .views import TemplateDetailView, TemplateCompileView

urlpatterns = [
    path('templates/<str:name>/', TemplateDetailView.as_view(), name='template-detail'),
    path('templates/<str:name>/compile/', TemplateCompileView.as_view(), name='template-compile'),
]