from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Shop Management'

    def ready(self):
        """Import signals when the app is ready"""
        import shop.signals  # noqa
