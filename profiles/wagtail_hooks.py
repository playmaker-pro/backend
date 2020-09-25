from django.utils.html import format_html

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from .models import Profile, PlayerProfile, CoachProfile, CoachProfile, RoleChangeRequest


class ProfileAdminBase(ModelAdmin):
    """Profile base admin."""

    model = Profile
    menu_label = "Profiles"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_filter = ("email_verified",)
    list_display = ("bio", "user", "permalink",)
    search_fields = ("bio", "user",)

    def permalink(self, obj):
        url =  ' dummy link to profile' #reverse("profiles:show", kwargs={"slug": obj.profile.slug})  @todo - set proper link to profile show
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))


class RegularProfileAdmin(ProfileAdminBase):
    model = Profile
    menu_label = 'regulars'
    

class PlayerProfileAdmin(ProfileAdminBase): 
    model = PlayerProfile
    menu_label = 'players'
    menu_order = 100


class CoachProfileAdmin(ProfileAdminBase): 
    model = CoachProfile
    menu_label = 'coaches'
    menu_order = 200


class RoleChangeAdmin(ModelAdmin): 
    model = RoleChangeRequest
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