from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from .models import LegalBasis


# Lists legal basis records and supports filtering by reference type.
def legal_basis_list(request):
    reference_type = request.GET.get('type', '')
    allowed_types = {value for value, _ in LegalBasis.REFERENCE_TYPE_CHOICES}

    if reference_type and reference_type not in allowed_types:
        return HttpResponseBadRequest('Invalid legal basis type.')

    legal_bases = LegalBasis.objects.all()
    if reference_type:
        legal_bases = legal_bases.filter(reference_type=reference_type)

    context = {
        'legal_bases': legal_bases,
        'reference_type': reference_type,
        'reference_type_choices': LegalBasis.REFERENCE_TYPE_CHOICES,
    }
    return render(request, 'legal_basis/list.html', context)


# Shows one legal basis record used by detail pages and related office/plantilla references.
def legal_basis_detail(request, pk):
    legal_basis = get_object_or_404(LegalBasis, pk=pk)
    return render(request, 'legal_basis/detail.html', {'legal_basis': legal_basis})
