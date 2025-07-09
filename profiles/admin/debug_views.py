# # Tymczasowy uproszczony PlayerProfileAdmin do debugowania
# from django.contrib import admin

# from profiles import models
# from profiles.admin.views import ProfileAdminBase


# # Tymczasowa uproszczona wersja do debugowania
# @admin.register(models.PlayerProfile)
# class PlayerProfileAdminDebug(ProfileAdminBase):
#     """Uproszczona wersja do debugowania problemów z ładowaniem"""

#     list_display = ("pk", "user", "slug", "active")

#     # Minimalna lista pól
#     autocomplete_fields = ("user",)

#     readonly_fields = ("uuid",)

#     search_fields = ("user__email", "user__first_name", "user__last_name")

#     # Brak actions żeby sprawdzić czy to nie one powodują problem
#     actions = []

#     def get_queryset(self, request):
#         """Podstawowa optymalizacja"""
#         return super().get_queryset(request).select_related("user")
