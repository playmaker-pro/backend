from django.contrib import admin

from .models import Mapper, MapperEntity, MapperSource


class MapperEntityAdmin(admin.TabularInline):
    model = MapperEntity
    extra = 1
    readonly_fields = ("created_at", "updated_at")


class MapperAdmin(admin.ModelAdmin):
    inlines = [
        MapperEntityAdmin,
    ]
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Mapper, MapperAdmin)


@admin.register(MapperSource)
class MapperSourceAdmin(admin.ModelAdmin):
    pass
