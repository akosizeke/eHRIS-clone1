from django.urls import path

from . import views

app_name = 'core'

# Core app URL routes connected from the project root path in config/urls.py.
urlpatterns = [
    # Landing dashboard for the eHRIS system.
    path('', views.dashboard, name='dashboard'),
]
