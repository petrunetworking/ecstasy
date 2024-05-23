from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .new_permissions import create_permission

        post_migrate.connect(create_permission, sender=self)
