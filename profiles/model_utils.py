from profiles import forms

from . import models


def get_profile_model(user):
    if user.is_player:
        return models.PlayerProfile
    elif user.is_coach:
        return models.CoachProfile
    elif user.is_guest:
        return models.GuestProfile
    elif user.is_club:
        return models.ClubProfile
    elif user.is_scout:
        return models.ScoutProfile
    elif user.is_manager:
        return models.ManagerProfile
    else:
        return models.GuestProfile


def get_profile_model_from_slug(slug):
    default = (models.GuestProfile,)
    mapper = {
        "player": models.PlayerProfile,  # @todo te nazwy 'player' etc trzeba zastapic z roles.definitions...
        "coach": models.CoachProfile,
        "club": models.ClubProfile,
        "scout": models.ScoutProfile,
        "guest": models.GuestProfile,
        "manager": models.ManagerProfile,
    }

    for key, model in mapper.items():
        if slug.startswith(key):
            return model
    return default


def get_profile_form_model(user):
    if user.is_player:
        return forms.PlayerProfileForm

    elif user.is_coach:
        return forms.CoachProfileForm
    elif user.is_manager:
        return forms.ManagerProfileForm
    elif user.is_guest:
        return forms.GuestProfileForm
    elif user.is_club:
        return forms.ClubProfileForm

    elif user.is_scout:
        return forms.ScoutProfileForm
    else:
        return forms.ProfileForm
