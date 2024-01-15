from django.contrib import admin

from .models import ExternalLinks, ExternalLinksEntity, LinkSource


class ExternalLinksEntityAdmin(admin.TabularInline):
    model = ExternalLinksEntity
    extra = 1
    readonly_fields = ("created_at", "updated_at")


class ExternalLinksAdmin(admin.ModelAdmin):
    inlines = [
        ExternalLinksEntityAdmin,
    ]
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(ExternalLinks, ExternalLinksAdmin)


@admin.register(LinkSource)
class LinkSourceAdmin(admin.ModelAdmin):
    pass
