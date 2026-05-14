from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage

from .models import Organization


ORGANIZATION_FIELDS = (
    'name',
    'short_name',
    'province_code',
    'address',
    'seal_path',
    'is_active',
)


def serialize_organization(organization):
    seal_path = organization.seal_path or ''
    return {
        'id': str(organization.id),
        'name': organization.name,
        'short_name': organization.short_name,
        'province_code': organization.province_code,
        'address': organization.address,
        'seal_path': seal_path,
        'seal_url': default_storage.url(seal_path) if seal_path else '',
        'is_active': organization.is_active,
        'created_at': organization.created_at.isoformat(),
        'modified_at': organization.modified_at.isoformat(),
    }


def build_organization(data, organization=None, partial=False):
    if not isinstance(data, dict):
        raise ValidationError({'payload': 'Expected a JSON object.'})

    instance = organization or Organization()
    if not partial:
        missing_fields = [
            field for field in ORGANIZATION_FIELDS
            if field != 'is_active' and field not in data
        ]
        if missing_fields:
            raise ValidationError({
                field: 'This field is required.'
                for field in missing_fields
            })

    if organization is None and data.get('id'):
        try:
            instance.id = UUID(str(data['id']))
        except (TypeError, ValueError):
            raise ValidationError({'id': 'Organization id must be a valid UUID.'})

    if 'is_active' in data and not isinstance(data['is_active'], bool):
        raise ValidationError({'is_active': 'This field must be a boolean.'})

    for field in ORGANIZATION_FIELDS:
        if field in data:
            setattr(instance, field, data[field])

    instance.full_clean()
    return instance


def validation_error_to_dict(error):
    if hasattr(error, 'message_dict'):
        return error.message_dict
    return {'detail': error.messages}
