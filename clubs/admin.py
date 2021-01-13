

from django.contrib import admin
from users.queries import get_users_manger_roles
from . import models


@admin.register(models.Seniority)
class SeniorityAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.Gender)
class GenderAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'club', 'league', 'gender', 'seniority', 'manager')
    search_fields = ('name',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['manager'].queryset = get_users_manger_roles()
        form.base_fields['editors'].queryset = get_users_manger_roles()
        return form


@admin.register(models.Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'voivodeship', 'slug',)

    search_fields = ('name', )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['manager'].queryset = get_users_manger_roles()
        form.base_fields['editors'].queryset = get_users_manger_roles()
        return form