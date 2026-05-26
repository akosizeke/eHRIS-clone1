"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# Root URL router that connects each local app URL module to the site.
urlpatterns = [
    # Main dashboard route handled by apps.core.urls.
    path('', include('apps.core.urls')),
    # Legal basis pages and records.
    path('legal-basis/', include('apps.legal_basis.urls')),
    # Organization, office hierarchy, and office version workflows.
    path('organization/', include('apps.organization.urls')),
    # Plantilla item list, create, and detail workflows.
    path('plantilla/', include('apps.plantilla.urls')),
    # Django admin for registered models.
    path('admin/', admin.site.urls),
]

# Serves uploaded media locally while DEBUG is enabled.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
