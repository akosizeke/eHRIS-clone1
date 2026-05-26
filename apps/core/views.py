from django.shortcuts import render

from apps.legal_basis.models import LegalBasis
from apps.organization.models import Office, Organization


# Main dashboard view that summarizes organization, office, and legal basis records.
def dashboard(request):
    context = {
        'organization_count': Organization.objects.count(),
        'office_count': Office.objects.count(),
        'legal_basis_count': LegalBasis.objects.count(),
        'recent_legal_bases': LegalBasis.objects.all()[:5],
    }
    return render(request, 'core/dashboard.html', context)
