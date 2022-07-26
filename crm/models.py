from django.db import models
from django.conf import settings
from clubs.models import Team, Club
from django.utils.translation import gettext_lazy as _
from django.forms.models import model_to_dict
from datetime import datetime


class LeadStatus(models.Model):    

    FOLLOWED_FIELDS = [
        "id",
        "user",
        "club",
        "team",
        "first_name",
        "last_name",
        "phone",
        "email",
        "facebook_url",
        "twitter_url",
        "linkedin_url",
        "instagram_url",
        "website_url",
    ] 

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead",
        )
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_club",
        )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_team",
        )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        )    
    phone = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        )
    email = models.EmailField(null=True, blank=True)
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)
    twitter_url =  models.URLField(_("Twitter"), max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(_("Linkedin"), max_length=500, blank=True, null=True)
    instagram_url = models.URLField(_("Instagram"), max_length=500, blank=True, null=True)
    website_url = models.URLField(_("Website"), max_length=500, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_creator",
        )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_updater",
        )
    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of object placed in data_ database. It should alwayes reflect scheme which represents.",
    )
    is_actual = models.BooleanField(default=True)
    previous = models.OneToOneField(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="previous_version"
    )
    next = models.OneToOneField(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="next_version"
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)        
        instance._loaded_values = dict(zip(instance.FOLLOWED_FIELDS, values))        
        return instance

    def save(self, *args, **kwargs):
        cleaned_data = model_to_dict(self, fields=self.FOLLOWED_FIELDS)
        if not self._state.adding:
            data_changed = self.is_model_changed(self._loaded_values, cleaned_data)
            if data_changed:
                previous_obj = self
                if self.has_next():
                    previous_obj = self.get_child()
                new_model = LeadStatus.objects.create(
                    **self.parse_input(cleaned_data),
                    is_actual=True,
                    created_by=self.updated_by,
                    date_created=datetime.now(),
                    previous=previous_obj
                    )
                previous_obj.is_actual = False
                previous_obj.next = new_model
                previous_obj.date_updated = datetime.now()                
                previous_obj.save(*args, **kwargs)
        super().save(*args, **kwargs)


    def parse_input(self, input):
        input.pop("id")
        input["user_id"] = input.pop("user")
        input["club_id"] = input.pop("club")
        input["team_id"] = input.pop("team")
        return input

    def is_model_changed(self, pre_data, post_data):
        return pre_data != post_data

    def has_next(self):
        return self.next

    def get_child(self):
        if self.next:
            obj = self.next   
            return obj.get_child()
        return self
