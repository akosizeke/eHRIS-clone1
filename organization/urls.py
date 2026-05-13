from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/hierarchy/', views.office_hierarchy_index, name='office_hierarchy_index'),
    path('offices/<uuid:office_id>/hierarchy/', views.office_hierarchy, name='office_hierarchy'),
]
