import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import OfficeForm
from .models import Office


def dashboard(request):
    return render(request, 'dashboard.html')


def _office_to_dict(office):
    return {
        'id': str(office.id),
        'name': office.name,
        'office_code': office.office_code,
        'office_type': office.office_type,
        'level_no': office.level_no,
        'parent_office': office.parent_office.name if office.parent_office else None,
        'office_head': str(office.office_head_display) if office.office_head_display else '',
        'office_head_title': office.office_head_title,
        'is_active': office.is_active,
    }


def _node_to_dict(node):
    return {
        **_office_to_dict(node['office']),
        'children': [_node_to_dict(child) for child in node['children']],
    }


def _build_office_tree(root_office):
    active_offices = Office.objects.filter(
        organization=root_office.organization,
        is_active=True,
    ).select_related(
        'organization',
        'parent_office',
    ).order_by(
        'level_no',
        'name',
    )

    children_by_parent = defaultdict(list)
    for office in active_offices:
        children_by_parent[office.parent_office_id].append(office)

    def build_node(office, visited=None):
        visited = visited or set()
        if office.pk in visited:
            return {'office': office, 'children': []}
        visited.add(office.pk)
        return {
            'office': office,
            'children': [
                build_node(child, visited.copy())
                for child in children_by_parent.get(office.pk, [])
            ],
        }

    return build_node(root_office)


def office_hierarchy(request, office_id):
    office = get_object_or_404(
        Office.objects.select_related('organization', 'parent_office'),
        pk=office_id,
    )
    hierarchy = _build_office_tree(office)

    context = {
        'office': office,
        'hierarchy': hierarchy,
        'parent_office': office.parent_office,
        'child_offices': hierarchy['children'],
    }

    if _request_wants_json(request):
        return JsonResponse({
            'success': True,
            'office': _office_to_dict(office),
            'parent_office': _office_to_dict(office.parent_office) if office.parent_office else None,
            'hierarchy': _node_to_dict(hierarchy),
        })

    return render(request, 'organization/offices/hierarchy.html', context)


def _request_wants_json(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
        or request.content_type == 'application/json'
    )


def _errors_to_json(errors):
    return {
        field: [str(error) for error in field_errors]
        for field, field_errors in errors.items()
    }


@login_required
@permission_required('organization.add_office', raise_exception=True)
@require_http_methods(['GET', 'POST'])
def office_create(request):
    wants_json = _request_wants_json(request)

    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST

        form = OfficeForm(data)
        if form.is_valid():
            office = form.save()
            if wants_json:
                return JsonResponse({
                    'success': True,
                    'message': 'Office unit created successfully.',
                    'office': _office_to_dict(office),
                })
            messages.success(request, 'Office unit created successfully.')
            return redirect(reverse('organization:office_hierarchy', args=[office.pk]))

        if wants_json:
            return JsonResponse({
                'success': False,
                'errors': _errors_to_json(form.errors),
            }, status=400)

        messages.error(request, 'Please correct the errors below.')
    else:
        form = OfficeForm()

    return render(request, 'organization/offices/create.html', {'form': form})
