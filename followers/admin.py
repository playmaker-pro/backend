from django.contrib import admin

from followers.models import GenericFollow

# Register your models here.


@admin.register(GenericFollow)
class FollowAdmin(admin.ModelAdmin):
    pass