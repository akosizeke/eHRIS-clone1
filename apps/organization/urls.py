from django.urls import path

from . import views

app_name = 'organization'

urlpatterns = [
    path('', views.organization_list, name='list'),
    path('offices/', views.office_list, name='office_list'),
    path('offices/<uuid:pk>/', views.office_detail, name='office_detail'),
]
