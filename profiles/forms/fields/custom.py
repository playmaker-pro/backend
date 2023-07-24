from __future__ import unicode_literals
from django import forms
from django.utils.translation import gettext_lazy as _
from clubs.models import Club, TeamHistory
from clubs.models import TeamHistory as Team
from django.core.exceptions import ValidationError


class ModelChoiceFieldNoValidation(forms.ChoiceField):

    verification_model = TeamHistory

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = "pk"
            if isinstance(value, self.verification_model):
                value = getattr(value, key)
            value = self.verification_model.objects.get(**{key: value})
        except (ValueError, TypeError, self.verification_model.DoesNotExist):
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            )
        return value

    def validate(self, value):
        return True

    def valid_value(self, value):
        """Check to see if the provided value is a valid choice."""
        return True


class ClubModelChoiceFieldNoValidation(forms.ChoiceField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = "pk"
            if isinstance(value, Club):
                value = getattr(value, key)
            value = Club.objects.get(**{key: value})
        except (ValueError, TypeError, Club.DoesNotExist):
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            )
        return value

    def validate(self, value):
        return True

    def valid_value(self, value):
        """Check to see if the provided value is a valid choice."""
        return True
