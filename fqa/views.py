import logging
from django.contrib.auth import get_user_model
from django.views import generic
from app import mixins

from .models import QuestionAnswer

User = get_user_model()


logger = logging.getLogger(__name__)


class FaqView(
    generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin
):
    page_title = "Najczęściej zadawane pytania"
    template_name = "fqa/base.html"

    def get(self, request, *args, **kwargs):
        kwargs["objects"] = QuestionAnswer.objects.filter(visible=True)
        kwargs["page_title"] = self.page_title
        kwargs["modals"] = self.modal_activity(
            request.user, register_auto=False, verification_auto=False
        )
        return super().get(request, *args, **kwargs)
