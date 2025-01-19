from django.contrib import admin

from .models import ExternalLinks, ExternalLinksEntity, LinkSource


class ExternalLinksEntityInlineAdmin(admin.TabularInline):
    model = ExternalLinksEntity
    extra = 1
    readonly_fields = ("created_at", "updated_at")


@admin.register(ExternalLinksEntity)
class ExternalLinksEntityAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_display = ("pk", "owner", "source", "owner_type", "url")
    search_fields = ("description",)
    autocomplete_fields = ("target",)

    def owner(self, obj):
        return obj.target.owner

    def owner_type(self, obj):
        return obj.target.target_name


class ExternalLinksAdmin(admin.ModelAdmin):
    inlines = [
        ExternalLinksEntityInlineAdmin,
    ]
    list_display = ("pk", "owner", "created_at", "updated_at", "links_count")
    readonly_fields = ("created_at", "updated_at", "target_name")
    search_fields = (
        "playerprofile__slug",
        "clubprofile__slug",
        "coachprofile__slug",
        "guestprofile__slug",
        "managerprofile__slug",
        "scoutprofile__slug",
        "refereeprofile__slug",
        "club__name",
        "leaguehistory__name",
        "team__name",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def owner(self, obj):
        return obj.owner

    def links_count(self, obj):
        return obj.links.count()


admin.site.register(ExternalLinks, ExternalLinksAdmin)

#
# # @admin.register(LinkSource)
# class LinkSourceAdmin(admin.ModelAdmin):
#     search_fields = ("name",)
