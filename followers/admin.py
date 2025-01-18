from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from followers.models import GenericFollow

# Register your models here.


@admin.register(GenericFollow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "who",
        "followed",
        "created_at",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("user",)
    readonly_fields = (
        "content_type",
        "object_id",
        "content_object",
        "user",
        "created_at",
    )

    def followed(self, obj):
        user = obj.content_object.user
        view_name = (
            f"admin:{user._meta.app_label}_"  # noqa
            f"{user.__class__.__name__.lower()}_change"
        )
        link_url = reverse(view_name, args=[user.pk])
        return format_html(f'<a href="{link_url}">{user}</a>')

    def who(self, obj):
        user = obj.user
        view_name = (
            f"admin:{user._meta.app_label}_"  # noqa
            f"{user.__class__.__name__.lower()}_change"
        )
        link_url = reverse(view_name, args=[user.pk])
        return format_html(f'<a href="{link_url}">{user}</a>')
