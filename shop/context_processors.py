from .models import SiteSettings

def site_settings(request):
    """
    Context processor to make site settings available in all templates.
    """
    return {
        'settings': SiteSettings.get_settings()
    } 