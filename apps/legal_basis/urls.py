from django.urls import path

from . import views

app_name = 'legal_basis'

# Legal basis routes connected under /legal-basis/ in config/urls.py.
urlpatterns = [
    # List and filter legal basis records.
    path('', views.legal_basis_list, name='list'),
    # Detail page for one legal basis record by UUID.
    path('<uuid:pk>/', views.legal_basis_detail, name='detail'),
]
