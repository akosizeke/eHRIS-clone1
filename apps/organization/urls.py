from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # Organization routes
    path('organizations/', views.organization_page, name='organization_page'),
    path('organizations/api/', views.organization_collection, name='organization_collection'),
    path('organizations/api/<uuid:organization_id>/', views.organization_detail, name='organization_detail'),
    
    # Office routes
    path('offices/', views.office_hierarchy_index, name='office_hierarchy_index'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/<uuid:office_id>/', views.office_hierarchy, name='office_hierarchy'),
]
