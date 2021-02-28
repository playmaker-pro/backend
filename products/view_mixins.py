class ProductFilterMixn:

    @property
    def filter_tag(self):
        value = self.request.GET.get('tag')
        if value:
            return value
        return None
