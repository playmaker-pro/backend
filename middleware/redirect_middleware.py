class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Each request that comes to playmaker.pro is redirected to premiera.playmaker.pro"""
        if request.get_host() == "playmaker.pro":
            request.urlconf = "backend.redirect_urls"
        else:
            request.urlconf = "backend.urls"

        return self.get_response(request)
