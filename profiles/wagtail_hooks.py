from django.utils.html import format_html

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from django.urls import reverse
from . import models


class ProfileAdminBase(ModelAdmin):
    """Profile base admin."""

    model = models.GuestProfile
    menu_label = "Profiles"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_filter = ("email_verified",)
    list_display = ("bio", "user", "permalink",)
    search_fields = ("bio", "user",)

    def permalink(self, obj):
        url = reverse("profiles:show", kwargs={"slug": obj.slug})
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))


class RegularProfileAdmin(ProfileAdminBase):
    menu_label = 'guests'


class PlayerProfileAdmin(ProfileAdminBase):
    model = models.PlayerProfile
    menu_label = 'players'
    menu_order = 100


class CoachProfileAdmin(ProfileAdminBase):
    model = models.CoachProfile
    menu_label = 'coaches'
    menu_order = 200


class RoleChangeAdmin(ModelAdmin): 
    model = models.RoleChangeRequest
    menu_label = "Role Change Requests"
    menu_icon = "placeholder"
    menu_order = 600
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("user", "approved", "currnet", "new", "approver", "reuqest_date",)


class ProfilesAdminGroup(ModelAdminGroup):
    menu_label = 'Profiles'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (RegularProfileAdmin, PlayerProfileAdmin, CoachProfileAdmin, RoleChangeAdmin)


# When using a ModelAdminGroup class to group several ModelAdmin classes together,
# you only need to register the ModelAdminGroup class with Wagtail:
modeladmin_register(ProfilesAdminGroup)
