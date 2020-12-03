from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "profiles"

urlpatterns = [
    path("me/", views.ShowProfile.as_view(), name="show_self"),
    path("me/query/", views.inquiry, name="inquiry_me"),
    path("me/observe/", views.observe, name="observe_me"),
    path('me/verification/', views.AccountVerification.as_view(), name='account_verification'),
    path("me/edit/", views.EditProfile.as_view(), name="edit_self"),
    path("me/edit/settings/", views.EditAccountSettings.as_view(), name="edit_settings"),
    path('player/fantasy/', views.ProfileFantasy.as_view(), name='player_fantasy'),
    path('player/carrier/', views.ProfileCarrier.as_view(), name='player_carrier'),
    path('player/matches/', views.ProfileGames.as_view(), name='player_games'),
    path('my/observers/', views.ProfileObservers.as_view(), name='my_observers'),
    path('my/requests/', views.ProfileRequests.as_view(), name='my_requests'),
    path("me/changerole/", views.RequestRoleChange.as_view(), name="rolechange_self"),
    path("<slug:slug>/", views.ShowProfile.as_view(), name="show"),
    path("howto/process/", TemplateView.as_view(template_name='profiles/how_to.html'), name="howto"),
]
