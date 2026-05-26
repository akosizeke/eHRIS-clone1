from django.urls import path

from . import views

app_name = 'plantilla'

# Plantilla routes connected under /plantilla/ in config/urls.py.
urlpatterns = [
    # List and filter plantilla items.
    path('', views.plantilla_list, name='list'),
    # Create a new plantilla item linked to an office.
    path('create/', views.plantilla_create, name='create'),
    # View one plantilla item and its history.
    path('<uuid:pk>/', views.plantilla_detail, name='detail'),
]
