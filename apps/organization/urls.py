from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('offices/', views.office_hierarchy_index, name='office_hierarchy_index'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/<uuid:office_id>/', views.office_hierarchy, name='office_hierarchy'),
]
