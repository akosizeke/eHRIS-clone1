from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/<uuid:office_id>/hierarchy/', views.office_hierarchy, name='office_hierarchy'),
]
