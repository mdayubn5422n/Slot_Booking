class UTMMiddleware:
    """UTM tracking: if the web address has ?utm_source=...&utm_medium=...&utm_campaign=...,
    remember those values in the session so they can be saved with a booking or message."""

    KEYS = ("utm_source", "utm_medium", "utm_campaign")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        found = {k: request.GET[k][:100] for k in self.KEYS if request.GET.get(k)}
        if found:
            request.session["utm"] = found
        return self.get_response(request)
