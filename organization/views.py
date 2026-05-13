import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import OfficeForm
from .models import Office, Organization


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


def _office_matches_query(office, query):
    if not query:
        return True
    haystack = ' '.join([
        office.name or '',
        office.office_code or '',
        office.office_type or '',
        office.office_head_title or '',
        str(office.office_head_display or ''),
    ]).lower()
    return query.lower() in haystack


def _filter_tree(node, query):
    filtered_children = [
        child
        for child in (_filter_tree(child, query) for child in node['children'])
        if child is not None
    ]

    if _office_matches_query(node['office'], query) or filtered_children:
        return {
            'office': node['office'],
            'children': filtered_children,
        }
    return None


def _build_office_tree(root_office, query=''):
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

    tree = build_node(root_office)
    return _filter_tree(tree, query) if query else tree


def _hierarchy_create_url(organization=None):
    url = reverse('organization:office_create')
    if organization:
        return f'{url}?organization={organization.pk}'
    return url


def _related_offices(organization, selected_office=None):
    if not organization:
        return Office.objects.none()

    related = Office.objects.filter(
        organization=organization,
        is_active=True,
    ).order_by('level_no', 'name')

    if selected_office:
        related = related.exclude(pk=selected_office.pk)

    return related[:6]


def office_hierarchy_index(request):
    query = request.GET.get('q', '').strip()
    organization = Organization.objects.filter(is_active=True).order_by('name').first()
    office = None
    hierarchy = None

    if organization:
        office = Office.objects.filter(
            organization=organization,
            is_active=True,
            parent_office__isnull=True,
        ).select_related('organization', 'parent_office').order_by('level_no', 'name').first()

        if office is None:
            office = Office.objects.filter(
                organization=organization,
                is_active=True,
            ).select_related('organization', 'parent_office').order_by('level_no', 'name').first()

        if office:
            hierarchy = _build_office_tree(office, query=query)

    context = {
        'office': office,
        'organization': organization,
        'hierarchy': hierarchy,
        'parent_office': office.parent_office if office else None,
        'child_offices': hierarchy['children'] if hierarchy else [],
        'related_offices': _related_offices(organization, office),
        'query': query,
        'create_office_url': _hierarchy_create_url(organization),
        'new_office_form': OfficeForm(initial={'organization': organization} if organization else None),
    }

    if _request_wants_json(request):
        return JsonResponse({
            'success': True,
            'office': _office_to_dict(office) if office else None,
            'hierarchy': _node_to_dict(hierarchy) if hierarchy else None,
        })

    return render(request, 'organization/offices/hierarchy.html', context)


def office_hierarchy(request, office_id):
    query = request.GET.get('q', '').strip()
    office = get_object_or_404(
        Office.objects.select_related('organization', 'parent_office'),
        pk=office_id,
    )
    hierarchy = _build_office_tree(office, query=query)

    context = {
        'office': office,
        'organization': office.organization,
        'hierarchy': hierarchy,
        'parent_office': office.parent_office,
        'child_offices': hierarchy['children'] if hierarchy else [],
        'related_offices': _related_offices(office.organization, office),
        'query': query,
        'create_office_url': _hierarchy_create_url(office.organization),
        'new_office_form': OfficeForm(initial={'organization': office.organization}),
    }

    if _request_wants_json(request):
        return JsonResponse({
            'success': True,
            'office': _office_to_dict(office),
            'parent_office': _office_to_dict(office.parent_office) if office.parent_office else None,
            'hierarchy': _node_to_dict(hierarchy) if hierarchy else None,
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
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            hierarchy_office = office.parent_office or office
            return redirect(reverse('organization:office_hierarchy', args=[hierarchy_office.pk]))

        if wants_json:
            return JsonResponse({
                'success': False,
                'errors': _errors_to_json(form.errors),
            }, status=400)

        messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        organization_id = request.GET.get('organization')
        parent_id = request.GET.get('parent')
        if organization_id:
            initial['organization'] = organization_id
        if parent_id:
            initial['parent_office'] = parent_id
        form = OfficeForm(initial=initial)

    return render(request, 'organization/offices/create.html', {
        'form': form,
        'next_url': request.GET.get('next', ''),
        'hierarchy_url': reverse('organization:office_hierarchy_index'),
    })
