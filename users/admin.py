from django.contrib import admin
from django.contrib.admin import ChoicesFieldListFilter, SimpleListFilter
from django.contrib.auth.admin import UserAdmin  # as BaseUserAdmin
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Case, F, Q, QuerySet, When
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from utils import linkify

from . import models
from .forms import UserPreferencesForm


def verify_one(modeladmin, request, queryset):
    f = queryset.first()
    f.verify()
    f.save()


class VerificationFilter(ChoicesFieldListFilter):
    title = "Werifikacja"
    parameter_name = "Werifikacja"

    def lookups(self, request, model_admin):
        return [
            (1, '{player,coach} - dropdown - "" - hasMapperID'),
            (2, '{player,coach} - dropdown - "" - noMapperID'),
            (3, "{player,coach} - input - noTeamInDropdown - hasMapperID"),
            (4, "{player,coach} - input - noTeamInDropdown - noMapperID"),
            (5, "{player,coach} - input - hasNoTeamNow - noMapperID"),
            (6, "{player,coach} - input - hasNoTeamNow - hasMapperID"),
            (7, "{player,coach} - input - hasNoTeamNever - noMapperID"),
            (8, "{player,coach} - input - hasNoTeamNever - hasMapperID"),
            (9, '{club} - dropdown - "" - ""'),
            (10, '{club} - input - noTeamInDropdown - ""'),
            (11, '{club} - input - hasNoTeamNow - ""'),
            (12, '{club} - input - hasNoTeamNever - ""'),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related("coachprofile", "playerprofile").annotate(
            mapper_id=Case(
                When(
                    declared_role="T",
                    then=F("coachprofile__mapper__mapperentity__mapper_id"),
                ),
                When(
                    declared_role="P",
                    then=F("playerprofile__mapper__mapperentity__mapper_id"),
                ),
            ),
            team_club_league_voivodeship_ver=Case(
                When(
                    declared_role="C",
                    then=F("clubprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="T",
                    then=F("coachprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="P",
                    then=F("playerprofile__team_club_league_voivodeship_ver"),
                ),
            ),
        )

        # if self.value() in ['9', '10', '11', '12']:
        #     query = Q(declared_role__in=['C'])
        #     # queryset = queryset.filter(declared_role__in=['T', 'P'])
        # else:
        #     # queryset = queryset.filter(declared_role__in=['C'])
        #     query = Q(declared_role__in=['T', 'P'])

        if self.value() in ["1", "3", "6", "8"]:
            query = Q(mapper_id__isnull=False)
        else:
            query = Q(mapper_id__isnull=False)
            # queryset = queryset.filter(data_mapper_id__isnull=False)

        # if self.value() in ['3', '4', '5', '6', '7', '8', '10', '11', '12']:
        #     query &= Q(team_club_league_voivodeship_ver__isnull=False)
        # queryset = queryset.filter(team_club_league_voivodeship_ver__isnull=False)

        return queryset.filter(query)


class VerificationInputTypeFilter(SimpleListFilter):
    title = "VerificationInputType"
    parameter_name = "VerificationInputType"

    def lookups(self, request, model_admin):
        return [
            (1, "HasTextInput"),
            (2, "HasTeamObject"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related(
            "clubprofile", "coachprofile", "playerprofile"
        ).annotate(
            text_input=Case(
                When(
                    declared_role="C",
                    then=F("clubprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="T",
                    then=F("coachprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="P",
                    then=F("playerprofile__team_club_league_voivodeship_ver"),
                ),
                default=None,
            ),
            team_object=Case(
                When(declared_role="C", then=F("clubprofile__club_object")),
                When(declared_role="T", then=F("coachprofile__team_object")),
                When(declared_role="P", then=F("playerprofile__team_object")),
                default=None,
            ),
        )

        if self.value() == "1":
            queryset = queryset.filter(text_input__isnull=False)
        elif self.value() == "2":
            queryset = queryset.filter(team_object__isnull=False)
        return queryset


class HasDataMapperIdFilter(SimpleListFilter):
    title = "mapper Id"
    parameter_name = "mapper_id"

    def lookups(self, request, model_admin):
        return [
            (1, "hasMapperID"),
            (2, "noMapperID"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.distinct()
        if self.value() == "1":
            queryset = queryset.filter(
                Q(
                    declared_role="T",
                    coachprofile__mapper__mapperentity__mapper_id__isnull=False,
                    coachprofile__mapper__mapperentity__database_source="s38",
                )
                | Q(
                    declared_role="P",
                    playerprofile__mapper__mapperentity__mapper_id__isnull=False,
                    playerprofile__mapper__mapperentity__database_source="s38",
                )
            )
        elif self.value() == "2":
            queryset = queryset.exclude(
                Q(
                    declared_role="T",
                    coachprofile__mapper__mapperentity__mapper_id__isnull=False,
                )
                & Q(coachprofile__mapper__mapperentity__database_source="s38")
            ).exclude(
                Q(
                    declared_role="P",
                    playerprofile__mapper__mapperentity__mapper_id__isnull=False,
                )
                & Q(playerprofile__mapper__mapperentity__database_source="s38")
            )
        return queryset


@admin.register(models.User)
class UserAdminPanel(UserAdmin):
    fieldsets = (
        (None, {"fields": ("password",)}),  # 'username',
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "userpreferences",
                    "profile",
                )
            },
        ),
        (
            _("Piłkarskie fakty"),
            {
                "fields": (
                    "declared_role",
                    "state",
                    "display_status",
                    "picture",
                    "declared_club",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "userpreferences",
                ),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "profile",
        "state",
        "display_status",
        "is_active",
        "last_login",
        "date_joined",
        "get_profile_permalink",
        linkify("profile"),
        "get_profile_percentage",
        "declared_role",
        "get_mapper",
        "get_team_object",
        "get_team_club_league_voivodeship_ver",
        "last_activity",
    )
    list_filter = ("state", "declared_role", HasDataMapperIdFilter)
    search_fields = ("username", "first_name", "last_name", "declared_role")
    readonly_fields = ("userpreferences", "profile")
    actions = [verify_one]

    def get_team_object(self, obj):
        if obj.is_club:
            if obj.profile and obj.profile.club_object:
                return obj.profile.club_object
        elif obj.is_coach or obj.is_player:
            if obj.profile and obj.profile.team_object:
                return obj.profile.team_object

    def get_team_club_league_voivodeship_ver(self, obj):
        try:
            return obj.profile.team_club_league_voivodeship_ver
        except:
            return ""

    def profile(self, obj):
        if profile := obj.profile:
            view_name = (
                f"admin:{profile._meta.app_label}_"  # noqa
                f"{profile.__class__.__name__.lower()}_change"
            )
            link_url = reverse(view_name, args=[profile.pk])
            return format_html(f'<a href="{link_url}">{profile}</a>')

    def get_mapper(self, obj):
        if hasattr(obj.profile, "mapper"):
            if obj.profile.mapper is not None:
                old_mapper = obj.profile.mapper.get_entity(
                    related_type__in=["player", "coach"], database_source="s38"
                )
                if old_mapper is not None:
                    return old_mapper.mapper_id
        return None

    def get_profile_percentage(self, obj):
        if obj.profile:
            percentage = obj.profile.percentage_completion
            return format_html(
                f"""
                <progress value="{percentage}" max="100"></progress>
                <span style="font-weight:bold">{percentage}%</span>
                """
            )

    get_profile_percentage.short_description = "Profile %"

    def get_profile_permalink(self, obj):
        if obj.profile:
            url = obj.profile.get_permalink
            return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))

    get_profile_permalink.short_description = "Profile Link"

    def get_profile(self, obj):
        if obj.profile is not None:
            return obj.profile.PROFILE_TYPE
        else:
            return "missing profile"

    get_profile.short_description = "Profile Type"


@admin.register(models.UserPreferences)
class UserPreferencesAdminPanel(admin.ModelAdmin):
    list_display = ("user", "localization", "display_languages", "citizenship")
    search_fields = ("user__last_name", "user__email")
    form = UserPreferencesForm
    autocomplete_fields = ("user",)

    def display_languages(self, obj):
        return ", ".join([str(language) for language in obj.spoken_languages.all()])

    display_languages.short_description = "Spoken Languages"

    def get_search_results(
        self,
        request: WSGIRequest,
        queryset: QuerySet[models.UserPreferences],
        search_term: str,
    ):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Custom search logic
        user_query = Q(user__username__icontains=search_term) | Q(
            user__email__icontains=search_term
        )
        queryset |= self.model.objects.filter(user_query)

        return queryset, use_distinct


class UserRefInline(admin.TabularInline):
    model = models.UserRef
    extra = 0
    fields = ("user", "ref_by", "has_bought_premium", "created_at")
    readonly_fields = ("ref_by", "user", "created_at", "has_bought_premium")
    show_change_link = True
    can_delete = False

    def has_bought_premium(self, obj):
        return obj.bought_premium


@admin.register(models.Ref)
class RefAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        linkify("user"),
        "ref_count",
        "premium_ref_count",
    )
    inlines = [UserRefInline]
    ordering = ("-referrals",)
    search_fields = (
        "uuid",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("user",)
    ordering = ("referrals",)
    readonly_fields = ("uuid", "user")

    def ref_count(self, obj):
        return len(obj.registered_users)

    def premium_ref_count(self, obj):
        if obj.registered_users:
            return len(obj.registered_users_premium)
        return 0


@admin.register(models.UserRef)
class UserRefAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        linkify("user"),
        linkify("ref_by"),
        "created_at",
        "has_bought_premium",
    )
    search_fields = ("user__first_name", "user__last_name", "ref_by")
    autocomplete_fields = ("user", "ref_by")
    readonly_fields = ("user", "ref_by", "created_at", "has_bought_premium")

    def has_bought_premium(self, obj):
        return obj.bought_premium
