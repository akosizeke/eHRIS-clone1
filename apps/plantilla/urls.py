from django.urls import path

from . import views

app_name = 'plantilla'

urlpatterns = [
    path('', views.plantilla_list, name='list'),
    path('create/', views.plantilla_create, name='create'),
    path('<uuid:pk>/', views.plantilla_detail, name='detail'),
]
