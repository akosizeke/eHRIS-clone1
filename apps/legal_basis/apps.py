from django.apps import AppConfig


# Django app configuration for legal basis records.
class LegalBasisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.legal_basis'  # ← dating 'legal_basis' lang
