from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('list/', views.organization_page, name='list'),

    # Organization routes
    path('organizations/', views.organization_page, name='organization_page'),
    path('api/organizations/', views.organization_collection, name='organization_collection'),
    path('api/organizations/<uuid:organization_id>/', views.organization_detail, name='organization_detail'),

    # Office routes
    path('offices/list/', views.office_hierarchy_index, name='office_list'),
    path('offices/', views.office_hierarchy_index, name='office_hierarchy_index'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/detail/<uuid:office_id>/', views.office_hierarchy, name='office_detail'),
    path('offices/<uuid:office_id>/versions/create/', views.office_version_create, name='office_version_create_for_office'),
    path('offices/<uuid:office_id>/versions/<uuid:version_id>/', views.office_version_detail, name='office_version_detail'),
    path('offices/<uuid:office_id>/', views.office_hierarchy, name='office_hierarchy'),
]
