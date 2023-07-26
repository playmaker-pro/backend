from django.views.generic import TemplateView


class ProductView(TemplateView):
    template_name = "premium/product_base.html"
