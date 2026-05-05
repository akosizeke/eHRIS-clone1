from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from .models import Item


def item_list(request):
    status = request.GET.get('status', '')
    allowed_statuses = {value for value, _ in Item.POSITION_STATUS_CHOICES}

    if status and status not in allowed_statuses:
        return HttpResponseBadRequest('Invalid plantilla status.')

    items = Item.objects.select_related('office', 'legalbasis')
    if status:
        items = items.filter(position_status=status)

    context = {
        'items': items,
        'status': status,
        'status_choices': Item.POSITION_STATUS_CHOICES,
    }
    return render(request, 'plantilla/list.html', context)


def item_detail(request, pk):
    item = get_object_or_404(
        Item.objects.select_related('office', 'legalbasis').prefetch_related('history'),
        pk=pk,
    )
    return render(request, 'plantilla/detail.html', {'item': item})
