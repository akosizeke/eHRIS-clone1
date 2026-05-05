from django.urls import path

from . import views

app_name = 'legal_basis'

urlpatterns = [
    path('', views.legal_basis_list, name='list'),
    path('<uuid:pk>/', views.legal_basis_detail, name='detail'),
]
