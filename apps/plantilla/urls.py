from django.urls import path

from . import views

app_name = 'plantilla'

urlpatterns = [
    path('', views.item_list, name='list'),
    path('<uuid:pk>/', views.item_detail, name='detail'),
]
