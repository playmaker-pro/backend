from django.http import HttpRequest


class RemoveM2MDuplicatesMixin:
    def changelist_view(self, request: HttpRequest, extra_context=None) -> HttpRequest:
        """Remove duplicates from ManyToMany fields in changelist view."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, "context_data") and "cl" in response.context_data:
            queryset = response.context_data["cl"].queryset

            # Remove duplicates using set operations after fetching queryset
            unique_results = list({item.id: item for item in queryset}.values())
            response.context_data["cl"].result_list = unique_results

        return response
