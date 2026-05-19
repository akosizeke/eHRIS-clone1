import json
from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import OfficeForm, OfficeVersionForm
from .models import Office, OfficeVersion, Organization
from .serializers import (
    build_organization,
    serialize_organization,
    validation_error_to_dict,
)


def dashboard(request):
    return render(request, 'dashboard.html')


# =========================================================
# ORGANIZATION VIEWS
# =========================================================

@require_http_methods(['GET'])
def organization_page(request):
    return render(request, 'organization/organizations.html')


def _json_payload(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise ValidationError({'payload': f'Invalid JSON: {exc.msg}.'})


def _save_seal_upload(uploaded_file):
    content_type = getattr(uploaded_file, 'content_type', '')

    if content_type and not content_type.startswith('image/'):
        raise ValidationError({'seal_path': 'Seal must be an image file.'})

    return default_storage.save(f'seals/{uploaded_file.name}', uploaded_file)


def _request_payload(request):
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.POST.dict()

        if 'seal_path' in request.FILES:
            data['seal_path'] = _save_seal_upload(request.FILES['seal_path'])

        return data

    return _json_payload(request)


def _include_inactive(request):
    return request.GET.get('include_inactive', '').lower() in {'1', 'true', 'yes'}


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def organization_collection(request):
    if request.method == 'GET':
        try:
            organizations = Organization.objects.all().order_by('name')

            if not _include_inactive(request):
                organizations = organizations.filter(is_active=True)

            return JsonResponse({
                'results': [
                    serialize_organization(organization)
                    for organization in organizations
                ]
            })

        except DatabaseError:
            return JsonResponse({
                'errors': {
                    'database': [
                        'Organization table is unavailable. Apply migrations first.'
                    ]
                }
            }, status=503)

    try:
        organization = build_organization(_request_payload(request))
        organization.save()

    except ValidationError as exc:
        return JsonResponse({
            'errors': validation_error_to_dict(exc)
        }, status=400)

    except DatabaseError:
        return JsonResponse({
            'errors': {
                'database': [
                    'Organization table is unavailable. Apply migrations first.'
                ]
            }
        }, status=503)

    return JsonResponse(serialize_organization(organization), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def organization_detail(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)

    if request.method == 'GET':
        if not organization.is_active and not _include_inactive(request):
            return JsonResponse({
                'errors': {
                    'detail': ['Organization not found.']
                }
            }, status=404)

        return JsonResponse(serialize_organization(organization))

    if request.method == 'DELETE':
        organization.is_active = False
        organization.save(update_fields=['is_active', 'modified_at'])

        return JsonResponse(serialize_organization(organization))

    try:
        organization = build_organization(
            _request_payload(request),
            organization=organization,
            partial=request.method == 'PATCH',
        )
        organization.save()

    except ValidationError as exc:
        return JsonResponse({
            'errors': validation_error_to_dict(exc)
        }, status=400)

    except DatabaseError:
        return JsonResponse({
            'errors': {
                'database': [
                    'Organization table is unavailable. Apply migrations first.'
                ]
            }
        }, status=503)

    return JsonResponse(serialize_organization(organization))


# =========================================================
# OFFICE HELPER FUNCTIONS
# =========================================================

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
            return {
                'office': office,
                'children': [],
            }

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


def _office_versions(office):
    if not office:
        return OfficeVersion.objects.none()

    return OfficeVersion.objects.filter(
        office_id=office,
    ).select_related(
        'legal_basis',
    ).order_by(
        '-effective_start_date',
        '-version_no',
    )


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


# =========================================================
# OFFICE VIEWS
# =========================================================

def office_hierarchy_index(request):
    query = request.GET.get('q', '').strip()

    organization = Organization.objects.filter(
        is_active=True,
    ).order_by('name').first()

    office = None
    hierarchy = None

    if organization:
        office = Office.objects.filter(
            organization=organization,
            is_active=True,
            parent_office__isnull=True,
        ).select_related(
            'organization',
            'parent_office',
        ).order_by(
            'level_no',
            'name',
        ).first()

        if office is None:
            office = Office.objects.filter(
                organization=organization,
                is_active=True,
            ).select_related(
                'organization',
                'parent_office',
            ).order_by(
                'level_no',
                'name',
            ).first()

        if office:
            hierarchy = _build_office_tree(office, query=query)

    context = {
        'office': office,
        'organization': organization,
        'hierarchy': hierarchy,
        'parent_office': office.parent_office if office else None,
        'child_offices': hierarchy['children'] if hierarchy else [],
        'related_offices': _related_offices(organization, office),
        'office_versions': _office_versions(office),
        'query': query,
        'create_office_url': _hierarchy_create_url(organization),
        'create_office_version_url': reverse('organization:office_version_create_for_office', args=[office.pk]) if office else '',
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
        is_active=True,
    )

    hierarchy = _build_office_tree(office, query=query)

    context = {
        'office': office,
        'organization': office.organization,
        'hierarchy': hierarchy,
        'parent_office': office.parent_office,
        'child_offices': hierarchy['children'] if hierarchy else [],
        'related_offices': _related_offices(office.organization, office),
        'office_versions': _office_versions(office),
        'query': query,
        'create_office_url': _hierarchy_create_url(office.organization),
        'create_office_version_url': reverse('organization:office_version_create_for_office', args=[office.pk]),
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

            return redirect(reverse(
                'organization:office_hierarchy',
                args=[hierarchy_office.pk],
            ))

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


def office_version_detail(request, office_id, version_id):
    office = get_object_or_404(Office, pk=office_id, is_active=True)
    version = get_object_or_404(
        OfficeVersion.objects.select_related('office_id', 'legal_basis'),
        pk=version_id,
        office_id=office,
    )

    return render(request, 'organization/office_versions/detail.html', {
        'office': office,
        'version': version,
    })


@require_http_methods(['GET', 'POST'])
def office_version_create(request, office_id):
    office = get_object_or_404(Office, pk=office_id, is_active=True)

    if request.method == 'POST':
        form = OfficeVersionForm(request.POST, office=office)
        if form.is_valid():
            form.save()
            return redirect(reverse('organization:office_hierarchy', args=[office.pk]))
    else:
        form = OfficeVersionForm(office=office)

    return render(request, 'organization/office_versions/create.html', {
        'form': form,
        'office': office,
    })
