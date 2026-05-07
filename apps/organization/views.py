from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from .models import Office, Organization


def organization_list(request):
    organizations = Organization.objects.prefetch_related('offices')
    return render(request, 'organization/list.html', {'organizations': organizations})


def office_list(request):
    office_type = request.GET.get('type', '')
    allowed_types = {value for value, _ in Office.OFFICE_TYPE_CHOICES}

    if office_type and office_type not in allowed_types:
        return HttpResponseBadRequest('Invalid office type.')

    offices = Office.objects.select_related('organization', 'parent_office')
    if office_type:
        offices = offices.filter(office_type=office_type)

    context = {
        'offices': offices,
        'office_type': office_type,
        'office_type_choices': Office.OFFICE_TYPE_CHOICES,
    }
    return render(request, 'organization/office_list.html', context)


def office_detail(request, pk):
    office = get_object_or_404(
        Office.objects.select_related('organization', 'parent_office'),
        pk=pk,
    )
    return render(request, 'organization/office_detail.html', {'office': office})
