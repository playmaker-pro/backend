from django.contrib import admin
from django.utils.html import format_html
from utils import linkify

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'state', 'is_active', 'get_profile', 'get_profile_permalink', linkify('profile'), 'get_profile_percentage', 'declared_role')
    list_filter = ('state',)
    search_fields = ('username',)

    def get_profile_percentage(self, obj):
        percentage = obj.profile.percentage_completion
        return format_html(
            f'''
            <progress value="{percentage}" max="100"></progress>
            <span style="font-weight:bold">{percentage}%</span>
            ''')
    get_profile_percentage.short_description = 'Profile %'

    def get_profile_permalink(self, obj):
        url = obj.profile.get_permalink
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))

    get_profile_permalink.short_description = 'Profile Link'

    def get_profile(self, obj):
        if obj.profile is not None:
            return obj.profile.PROFILE_TYPE
        else:
            return 'missing profile'

    get_profile.short_description = 'Profile Type'
