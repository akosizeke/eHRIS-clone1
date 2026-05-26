from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ItemForm
from .models import Item


# Converts a plantilla item model into JSON for API-style responses.
def _item_payload(item):
    return {
        'id': str(item.id),
        'item_number': item.item_number,
        'position_title': item.position_title,
        'salary_grade': item.salary_grade,
        'office_id': str(item.office_id),
        'employment_type': item.employment_type,
        'funding_source': item.funding_source,
        'position_status': item.position_status,
        'legalbasis_id': str(item.legalbasis_id) if item.legalbasis_id else None,
        'created_at': item.created_at.isoformat(),
        'modified_at': item.modified_at.isoformat(),
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


# Lists plantilla items with optional employment type and status filters.
def plantilla_list(request):
    employment_type = request.GET.get('employment_type', '')
    position_status = request.GET.get('status', '')
    allowed_employment_types = {value for value, _ in Item.EMPLOYMENT_TYPE_CHOICES}
    allowed_statuses = {value for value, _ in Item.POSITION_STATUS_CHOICES}

    if employment_type and employment_type not in allowed_employment_types:
        return HttpResponseBadRequest('Invalid employment type.')

    if position_status and position_status not in allowed_statuses:
        return HttpResponseBadRequest('Invalid position status.')

    items = Item.objects.select_related('office', 'legalbasis')
    if employment_type:
        items = items.filter(employment_type=employment_type)
    if position_status:
        items = items.filter(position_status=position_status)

    if _request_wants_json(request):
        return JsonResponse({'results': [_item_payload(item) for item in items]})

    return render(request, 'plantilla/list.html', {
        'items': items,
        'employment_type': employment_type,
        'position_status': position_status,
        'employment_type_choices': Item.EMPLOYMENT_TYPE_CHOICES,
        'position_status_choices': Item.POSITION_STATUS_CHOICES,
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
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            if _request_wants_json(request):
                return JsonResponse(_item_payload(item), status=201)
            return redirect(reverse('plantilla:detail', args=[item.pk]))

        if _request_wants_json(request):
            return JsonResponse({
                'errors': {
                    field: [str(error) for error in errors]
                    for field, errors in form.errors.items()
                }
            }, status=400)
    else:
        form = ItemForm()

    return render(request, 'plantilla/create.html', {
        'form': form,
    })


# Detects whether the caller expects JSON instead of an HTML template.
def _request_wants_json(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
        or request.content_type == 'application/json'
    )
