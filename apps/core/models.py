from django.db import models
import uuid
from django.db import models

# Shared abstract model for UUID primary keys and audit timestamps.
class AbstractBaseModel(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Keeps this base class from creating its own database table.
        abstract = True
