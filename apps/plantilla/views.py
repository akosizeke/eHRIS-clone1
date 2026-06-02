import json

from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.organization.models import Office

from .forms import ItemForm, NonPlantillaEmployeeForm
from .models import Item, NonPlantillaEmployee


# Converts a plantilla item model into JSON for API-style responses.
def _item_payload(item):
    return {
        'id': str(item.id),
        'item_number': item.item_number,
        'employee_name': item.employee_name,
        'position_title': item.position_title,
        'salary_grade': item.salary_grade,
        'office_id': str(item.office_id),
        'employment_type': item.employment_type,
        'funding_source': item.funding_source,
        'position_status': item.position_status,
        'duties_responsibilities': item.duties_responsibilities,
        'legalbasis_id': str(item.legalbasis_id) if item.legalbasis_id else None,
        'created_at': item.created_at.isoformat(),
        'modified_at': item.modified_at.isoformat(),
    }


def _non_plantilla_payload(employee):
    return {
        'id': str(employee.id),
        'name': employee.name,
        'employee_type': employee.employee_type,
        'office_id': str(employee.office_id),
        'duration': employee.duration_display,
        'duration_value': employee.duration_value,
        'duration_unit': employee.duration_unit,
        'start_date': employee.start_date.isoformat(),
        'end_date': employee.end_date.isoformat() if employee.end_date else None,
        'eligible_for_permanent': employee.eligible_for_permanent,
        'created_at': employee.created_at.isoformat(),
        'modified_at': employee.modified_at.isoformat(),
    }


# Converts one plantilla history record into JSON for the detail endpoint.
def _history_payload(history):
    return {
        'id': str(history.id),
        'plantilla_item_id': str(history.plantilla_item_id),
        'old_salary_grade': history.old_salary_grade,
        'new_salary_grade': history.new_salary_grade,
        'old_office_id': str(history.old_office_id) if history.old_office_id else None,
        'new_office_id': str(history.new_office_id) if history.new_office_id else None,
        'change_type': history.change_type,
        'effective_date': history.effective_date.isoformat(),
        'legalbasis_id': str(history.legalbasis_id) if history.legalbasis_id else None,
        'created_at': history.created_at.isoformat(),
        'modified_at': history.modified_at.isoformat(),
    }


# Shows the three-tab Plantilla Management System page.
def plantilla_list(request):
    active_tab = request.GET.get('tab', 'offices')
    if active_tab not in {'offices', 'plantilla', 'non-plantilla'}:
        return HttpResponseBadRequest('Invalid plantilla tab.')

    offices = Office.objects.filter(is_active=True).order_by('level_no', 'name')
    office_search = request.GET.get('office_q', '').strip()
    search = request.GET.get('q', '').strip()
    office_id = request.GET.get('office', '').strip()
    position_status = request.GET.get('status', '').strip()
    salary_grade = request.GET.get('sg', '').strip()
    non_plantilla_type = request.GET.get('type', '').strip()

    allowed_statuses = {value for value, _ in Item.POSITION_STATUS_CHOICES}
    allowed_non_plantilla_types = {
        value for value, _ in NonPlantillaEmployee.EMPLOYEE_TYPE_CHOICES
    }

    if position_status and position_status not in allowed_statuses:
        return HttpResponseBadRequest('Invalid position status.')

    if salary_grade and not salary_grade.isdigit():
        return HttpResponseBadRequest('Invalid salary grade.')

    if non_plantilla_type and non_plantilla_type not in allowed_non_plantilla_types:
        return HttpResponseBadRequest('Invalid non-plantilla type.')

    permanent_items = Item.objects.filter(
        employment_type='permanent',
    ).select_related(
        'office',
        'legalbasis',
    ).order_by(
        'office__level_no',
        'office__name',
        'item_number',
    )

    office_rows = _office_rows(offices, office_search, permanent_items)

    filtered_items = permanent_items
    if search:
        filtered_items = filtered_items.filter(
            Q(employee_name__icontains=search)
            | Q(position_title__icontains=search)
            | Q(item_number__icontains=search)
        )
    if office_id:
        filtered_items = filtered_items.filter(office_id=office_id)
    if position_status:
        filtered_items = filtered_items.filter(position_status=position_status)
    if salary_grade:
        filtered_items = filtered_items.filter(salary_grade=int(salary_grade))

    non_plantilla_employees = NonPlantillaEmployee.objects.select_related(
        'office',
    ).order_by(
        'office__level_no',
        'office__name',
        'name',
    )
    if search:
        non_plantilla_employees = non_plantilla_employees.filter(name__icontains=search)
    if non_plantilla_type:
        non_plantilla_employees = non_plantilla_employees.filter(employee_type=non_plantilla_type)
    if office_id:
        non_plantilla_employees = non_plantilla_employees.filter(office_id=office_id)

    if _request_wants_json(request):
        return JsonResponse({
            'plantilla': [_item_payload(item) for item in filtered_items],
            'non_plantilla': [
                _non_plantilla_payload(employee)
                for employee in non_plantilla_employees
            ],
        })

    return render(request, 'plantilla/list.html', {
        'active_tab': active_tab,
        'office_rows': office_rows,
        'items': filtered_items,
        'non_plantilla_employees': non_plantilla_employees,
        'offices': offices,
        'office_search': office_search,
        'search': search,
        'office_id': office_id,
        'position_status': position_status,
        'salary_grade': salary_grade,
        'salary_grades': range(1, 34),
        'non_plantilla_type': non_plantilla_type,
        'position_status_choices': Item.POSITION_STATUS_CHOICES,
        'non_plantilla_type_choices': NonPlantillaEmployee.EMPLOYEE_TYPE_CHOICES,
    })


# Shows one plantilla item and its history, as HTML or JSON.
def plantilla_detail(request, pk):
    item = get_object_or_404(
        Item.objects.select_related('office', 'legalbasis').prefetch_related('history'),
        pk=pk,
    )
    payload = _item_payload(item)
    payload['history'] = [_history_payload(history) for history in item.history.all()]
    if _request_wants_json(request):
        return JsonResponse(payload)

    return render(request, 'plantilla/detail.html', {
        'item': item,
        'history': item.history.all(),
    })


# Creates a plantilla item through the ItemForm and redirects to its detail page.
def plantilla_create(request):
    if request.method == 'POST':
        data = _request_data(request)
        data = data.copy()
        data['employment_type'] = 'permanent'
        data['funding_source'] = 'PS'

        form = ItemForm(data)
        if form.is_valid():
            item = form.save()
            if _request_wants_json(request):
                return JsonResponse(_item_payload(item), status=201)
            return redirect(f"{reverse('plantilla:list')}?tab=plantilla")

        if _request_wants_json(request):
            return JsonResponse({
                'errors': {
                    field: [str(error) for error in errors]
                    for field, errors in form.errors.items()
                }
            }, status=400)
    else:
        form = ItemForm(initial={'employment_type': 'permanent', 'funding_source': 'PS'})

    _prepare_permanent_form(form)

    return render(request, 'plantilla/create.html', {
        'form': form,
        'title': 'Add Position',
        'submit_label': 'Save Position',
    })


def plantilla_update(request, pk):
    item = get_object_or_404(Item, pk=pk, employment_type='permanent')

    if request.method == 'POST':
        data = _request_data(request)
        data = data.copy()
        data['employment_type'] = 'permanent'
        data['funding_source'] = item.funding_source
        form = ItemForm(data, instance=item)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('plantilla:list')}?tab=plantilla")
    else:
        form = ItemForm(instance=item)

    _prepare_permanent_form(form)

    return render(request, 'plantilla/create.html', {
        'form': form,
        'title': 'Edit Position',
        'submit_label': 'Save Changes',
    })


def non_plantilla_create(request):
    if request.method == 'POST':
        form = NonPlantillaEmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('plantilla:list')}?tab=non-plantilla")
    else:
        form = NonPlantillaEmployeeForm()

    return render(request, 'plantilla/non_plantilla_form.html', {
        'form': form,
        'title': 'Add Non-Plantilla',
        'submit_label': 'Save Non-Plantilla',
    })


def non_plantilla_update(request, pk):
    employee = get_object_or_404(NonPlantillaEmployee, pk=pk)

    if request.method == 'POST':
        form = NonPlantillaEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('plantilla:list')}?tab=non-plantilla")
    else:
        form = NonPlantillaEmployeeForm(instance=employee)

    return render(request, 'plantilla/non_plantilla_form.html', {
        'form': form,
        'title': 'Edit Non-Plantilla',
        'submit_label': 'Save Changes',
    })


def _office_rows(offices, office_search, permanent_items):
    office_queryset = offices
    if office_search:
        office_queryset = office_queryset.filter(
            Q(name__icontains=office_search)
            | Q(office_code__icontains=office_search)
        )

    office_queryset = office_queryset.annotate(
        total_positions=Count(
            'plantilla_items',
            filter=Q(plantilla_items__employment_type='permanent'),
        ),
        filled_count=Count(
            'plantilla_items',
            filter=Q(
                plantilla_items__employment_type='permanent',
                plantilla_items__position_status='filled',
            ),
        ),
        vacant_count=Count(
            'plantilla_items',
            filter=Q(
                plantilla_items__employment_type='permanent',
                plantilla_items__position_status='vacant',
            ),
        ),
        abolished_count=Count(
            'plantilla_items',
            filter=Q(
                plantilla_items__employment_type='permanent',
                plantilla_items__position_status='abolished',
            ),
        ),
    )

    positions_by_office = {}
    office_ids = [office.pk for office in office_queryset]
    for item in permanent_items.filter(office_id__in=office_ids):
        positions_by_office.setdefault(item.office_id, []).append(item)

    return [
        {
            'office': office,
            'positions': positions_by_office.get(office.pk, []),
        }
        for office in office_queryset
    ]


def _prepare_permanent_form(form):
    form.fields['employment_type'].widget = form.fields['employment_type'].hidden_widget()
    form.fields['funding_source'].widget = form.fields['funding_source'].hidden_widget()


def _request_data(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return {}
    return request.POST


# Detects whether the caller expects JSON instead of an HTML template.
def _request_wants_json(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
        or request.content_type == 'application/json'
    )
