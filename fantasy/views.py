import logging
import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import F, Q, Value, Window
from django.db.models.functions import Concat, DenseRank
from django.utils.translation import gettext_lazy as _

from app import mixins
from app.base.views import BasePMView
from clubs.models import League, Season
from profiles.utils import get_datetime_from_age
from voivodeships.services import VoivodeshipService

from .models import PlayerFantasyRank

User = get_user_model()


logger = logging.getLogger(__name__)

FANTASY_CHOICES = ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"]


class FantasyView(BasePMView, mixins.ViewFilterMixin, mixins.FilterPlayerViewMixin):
    page_title = "Fantasy"
    template_name = "fantasy/base.html"
    paginate_limit = 20

    def filter_queryset(self, queryset):
        if self.filter_season_exact:
            queryset = queryset.filter(season__name=self.filter_season_exact)

        if self.filter_leg is not None:
            queryset = queryset.filter(
                player__playerprofile__prefered_leg=self.filter_leg
            )

        if self.filter_is_senior is not None:
            queryset = queryset.filter(senior=self.filter_is_senior)

        if self.filter_name_of_team is not None:
            queryset = queryset.filter(
                player__playerprofile__team_object__name__icontains=self.filter_name_of_team
            )

        if self.filter_league is not None:
            leagues = [league for league in self.filter_league]
            league = (
                Q(
                    player__playerprofile__team_object__league__highest_parent__name__icontains=league
                )
                for league in leagues
            )
            query = reduce(operator.or_, league)
            queryset = queryset.filter(query)

        if self.filter_first_last is not None:
            queryset = queryset.annotate(
                fullname=Concat("player__first_name", Value(" "), "player__last_name")
            )
            queryset = queryset.filter(fullname__icontains=self.filter_first_last)

        if self.filter_vivo is not None:
            vivos = [i for i in self.filter_vivo]
            clauses = (
                Q(player__playerprofile__team_object__club__voivodeship_obj__name=p)
                for p in vivos
            )
            query = reduce(operator.or_, clauses)
            queryset = queryset.filter(query)

        if self.filter_age_min is not None:
            mindate = get_datetime_from_age(self.filter_age_min)
            queryset = queryset.filter(
                player__playerprofile__birth_date__year__lte=mindate.year
            )

        if self.filter_age_max is not None:
            maxdate = get_datetime_from_age(self.filter_age_max)
            queryset = queryset.filter(
                player__playerprofile__birth_date__year__gte=maxdate.year
            )

        if self.filter_position is not None:
            queryset = queryset.filter(
                player__playerprofile__position_raw=self.filter_position
            )

        if self.filter_fantasy_position:
            queryset = queryset.filter(
                player__playerprofile__position_raw__in=self.filter_fantasy_position
            )
        return queryset

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            "season": list(Season.objects.values_list("name", flat=True)),
        }

    def get(self, request, format=None, *args, **kwargs):
        # players = PlayerFantasyRank.objects.all().order_by('score')
        queryset = PlayerFantasyRank.objects.annotate(
            place=Window(
                expression=DenseRank(),
                order_by=[
                    F("score").desc(),
                ],
            )
        )
        vivos = VoivodeshipService()
        queryset = self.filter_queryset(queryset)
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get("page") or 1
        page_obj = paginator.get_page(page_number)
        kwargs["page_obj"] = page_obj
        kwargs["vivos"] = vivos.get_voivodeships
        kwargs["filters"] = self.get_filters_values()
        kwargs["leagues"] = League.objects.is_top_parent()
        kwargs["positions"] = FANTASY_CHOICES
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        self.prepare_kwargs(kwargs)
        kwargs["modals"] = self.modal_activity(
            request.user, register_auto=False, verification_auto=False
        )
        return super().get(request, *args, **kwargs)
