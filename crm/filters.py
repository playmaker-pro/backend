from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from .models import Conversation

User = get_user_model()    

class HasPhone(SimpleListFilter):
    title = "nr telefonu"
    parameter_name = "phone"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko przypisane"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__phone__isnull=False)
            else:
                return queryset.filter(phone__isnull=False)
        return queryset


class IsActual(SimpleListFilter):
    title = "aktualnych kontaktów"
    parameter_name = "is_actual"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko aktualne"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__is_actual=True)
            else:    
                return queryset.filter(is_actual=True)
        return queryset


class HasEmail(SimpleListFilter):
    title = "adres e-mail"
    parameter_name = "email"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko przypisane"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__email__isnull=False)
            else:
                return queryset.filter(email__isnull=False)
        return queryset


class HasTeam(SimpleListFilter):
    title = "klubu"
    parameter_name = "club"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko posiadający"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__club__isnull=False)
            else:
                return queryset.filter(club__isnull=False)
        return queryset


class HasClub(SimpleListFilter):
    title = "drużyny"
    parameter_name = "team"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko posiadający"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__team__isnull=False)
            else:
                return queryset.filter(team__isnull=False)
        return queryset

        
class HasUser(SimpleListFilter):
    title = "użytkownika"
    parameter_name = "user"

    def lookups(self, request, model_admin):
        return [
            (1, "Tylko przypisani"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":  
            if queryset.model is Conversation:
                return queryset.filter(lead__user__isnull=False)
            else:
                return queryset.filter(user__isnull=False)
        return queryset


class CreatedBy(SimpleListFilter):
    title = "kto utworzył kontakt"
    parameter_name = "created_by"

    def lookups(self, request, model_admin):
        return [
            (i+1, user) for i, user in 
                enumerate(User.objects.filter(groups__name__in=["CRM Admin"]))
            ]

    def queryset(self, request, queryset):
        if self.value():
            _, user = self.lookup_choices[int(self.value())-1]
            if queryset.model is Conversation:
                return queryset.filter(lead__created_by=user)
            else:
                return queryset.filter(
                    created_by=user
                    )
        return queryset