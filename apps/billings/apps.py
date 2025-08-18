from django.apps import AppConfig


class BillingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billings'

    def ready(self) -> None:
        ''' Load the Bbillings App Signals. '''
        from apps.billings import signals
        return super().ready()