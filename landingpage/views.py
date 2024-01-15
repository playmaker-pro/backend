from django.views import generic

from .forms import LandingpageForm


class LandingPage(generic.FormView):
    template_name = "landingpage/first_section.html"
    form_class = LandingpageForm


class WeGotIt(generic.TemplateView):
    template_name = "landingpage/we_got_it.html"


class WeGotItSuccess(generic.TemplateView):
    template_name = "landingpage/we_got_it_success.html"
