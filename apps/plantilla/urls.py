from django.urls import path

from . import views

app_name = 'plantilla'

# Plantilla routes connected under /plantilla/ in config/urls.py.
urlpatterns = [
    # List and filter plantilla items.
    path('', views.plantilla_list, name='list'),
    # Salary grade table placeholder page.
    path('salary-grade/', views.salary_grade, name='salary_grade'),
    # Download the salary grade table as an Excel workbook.
    path('salary-grade/export/', views.salary_grade_export, name='salary_grade_export'),
    # Upload an Excel workbook into the salary grade table.
    path('salary-grade/import/', views.salary_grade_import, name='salary_grade_import'),
    # Create a new plantilla item linked to an office.
    path('create/', views.plantilla_create, name='create'),
    # Edit one permanent plantilla position.
    path('<uuid:pk>/edit/', views.plantilla_update, name='edit'),
    # Create and edit non-plantilla employees.
    path('non-plantilla/create/', views.non_plantilla_create, name='non_plantilla_create'),
    path('non-plantilla/<uuid:pk>/edit/', views.non_plantilla_update, name='non_plantilla_edit'),
    # View one plantilla item and its history.
    path('<uuid:pk>/', views.plantilla_detail, name='detail'),
]
