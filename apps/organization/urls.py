from django.urls import path
from . import views

app_name = 'organization'

# Organization app routes connected under /organization/ in config/urls.py.
urlpatterns = [
    # Redirects the organization index to the main dashboard.
    path('', views.dashboard, name='dashboard'),

    # Organization routes
    # HTML page for managing organization records.
    path('list/', views.organization_page, name='list'),
    # Alternate HTML route for the same organization management page.
    path('organizations/', views.organization_page, name='organization_page'),
    # Legacy API endpoint for listing and creating organizations.
    path('api/organizations/', views.organization_collection, name='organization_collection_legacy'),
    # Legacy API endpoint for organization detail/update/deactivate.
    path('api/organizations/<uuid:organization_id>/', views.organization_detail, name='organization_detail_legacy'),
    # Current API endpoint for listing and creating organizations.
    path('organizations/api/', views.organization_collection, name='organization_collection'),
    # Current API endpoint for organization detail/update/deactivate.
    path('organizations/api/<uuid:organization_id>/', views.organization_detail, name='organization_detail'),

    # Office routes
    # Office hierarchy landing page.
    path('offices/list/', views.office_hierarchy_index, name='office_list'),
    # Alternate office hierarchy landing page.
    path('offices/', views.office_hierarchy_index, name='office_hierarchy_index'),
    # Office creation form for departments, divisions, and units.
    path('offices/create/', views.office_create, name='office_create'),
    # Legacy detail route for one office hierarchy node.
    path('offices/detail/<uuid:office_id>/', views.office_hierarchy, name='office_detail'),
    # Creates an OfficeVersion for the selected office.
    path('offices/<uuid:office_id>/versions/create/', views.office_version_create, name='office_version_create_for_office'),
    # Shows one OfficeVersion record.
    path('offices/<uuid:office_id>/versions/<uuid:version_id>/', views.office_version_detail, name='office_version_detail'),
    # Shows an office and its hierarchy.
    path('offices/<uuid:office_id>/', views.office_hierarchy, name='office_hierarchy'),
]
