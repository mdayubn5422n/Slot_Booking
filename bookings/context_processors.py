from django.conf import settings


def site_info(request):
    """Values every template can use: {{ SITE_NAME }} and {{ SITE_LAST_UPDATED }}."""
    return {"SITE_NAME": settings.SITE_NAME, "SITE_LAST_UPDATED": settings.SITE_LAST_UPDATED}
