from django.urls import path

from . import views

app_name = 'plantilla'

urlpatterns = [
    path('', views.plantilla_list, name='list'),
    path('<uuid:pk>/', views.plantilla_detail, name='detail'),
]
