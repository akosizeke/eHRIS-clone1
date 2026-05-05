from django.shortcuts import render

from apps.legal_basis.models import LegalBasis
from apps.organization.models import Office, Organization
from apps.plantilla.models import Item


def dashboard(request):
    context = {
        'organization_count': Organization.objects.count(),
        'office_count': Office.objects.count(),
        'legal_basis_count': LegalBasis.objects.count(),
        'plantilla_count': Item.objects.count(),
        'recent_legal_bases': LegalBasis.objects.all()[:5],
        'recent_items': Item.objects.select_related('office').all()[:5],
    }
    return render(request, 'core/dashboard.html', context)
