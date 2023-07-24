from collections import defaultdict

# from data.models import TeamStat  DEPRECATED: PM-1015
import utils

# from stats import utilites as utils    DEPRECATED: PM-1015

# class CoachSeasonSerializer:
#     def serialize(self, queryset):
#         data = defaultdict(lambda: 0)
#         for ps in queryset:
#             data["minutes_played"] += ps.minutes_played
#             data["team_goals"] += ps.team_goals
#             data["yellow_cards"] += ps.yellow_cards
#             data["red_cards"] += ps.red_cards

#             data["games_played"] += 1

#             if ps.minutes_played > 45:
#                 data["first_squad_games_played"] += 1
#             else:
#                 data["first_squad_games_played"] += 0

#             if ps.minutes_played > 0 and ps.minutes_played <= 45:
#                 data["from_bench"] += 1
#             else:
#                 data["from_bench"] += 0

#             if ps.minutes_played == 0:
#                 data["bench"] += 1
#             else:
#                 data["bench"] += 0

#         return data


class GameSerializer:
    def __init__(self, obj):
        self.data = {
            "date": self.get_date(obj),
            "date_short": self.get_date_short(obj),
            "date_year": self.get_date_year(obj),
            "guest_team_name": obj.guest_team_name,
            "host_team_name": obj.host_team_name,
            "host_score": self.get_host_score(obj),
            "guest_score": self.get_guest_score(obj),
            "league_name": self.get_league_name(obj),
        }

    def get_league_name(self, obj):
        code = obj.league.code
        name = obj.league.name
        return utils.translate_league_name(code, name)

    def get_date(self, obj):
        return obj.date.strftime("%Y-%m-%d")

    def get_date_short(self, obj):
        return obj.date.strftime("%m/%d")

    def get_date_year(self, obj):
        return obj.date.strftime("%Y")

    def get_host_score(self, obj):
        return obj.host_score

    def get_guest_score(self, obj):
        return obj.guest_score


class TeamStatSerializer:
    """
    game = models.ForeignKey("Game", on_delete=models.CASCADE, related_name="teamstat")
    team = models.ForeignKey("Team", on_delete=models.CASCADE, related_name="teamstats")
    coach = models.ForeignKey(
        "Coach", on_delete=models.CASCADE, related_name="coachstats", null=True, blank=True
    )
    # calcuable fields
    # auto-calculated fields on save

    result = models.IntegerField(default=-1, help_text='1 meas won, 0 means draw, 2 means lost , -1 is default')
    side = models.IntegerField(default=-1, help_text='0-host, 1-guest -1 error')
    points = models.IntegerField(default=0, help_text='3ptk won, 1ptk draw, 0ptk lost')
    lost_goals = models.IntegerField(default=0)
    gain_goals = models.IntegerField(default=0)


    Celem jest możliwość pokazania:
    kariera [sezon, team, rozgrywki, wygrane mecze, remisy, porażki, śr. pkt na mecz,  bramki strzelone vs. bramki stracone (klubu, który prowadził)]
    mecze [data, rozgrywki, gospodarz, gość, wynik]

    Za wygrany mecz 3 pkt, za remis 1 pkt, za porażkę 0 pkt.


    {"date": "2021-08-15",
    "goals": 0, "result": {"name": "W", "type": "won"},
    "date_year": "2021", "red_cards": 0, "team_name": "zagłębie lubin",
    "clear_goal": null, "date_short": "08/15", "host_score": 2,
    "team_goals": 0,
    "guest_score": 0,
    "league_name": "Ekstraklasa",
    "yellow_cards": 0, "host_team_name": "ZAGŁĘBIE LUBIN",
    "minutes_played": 23, "guest_team_name": "Pogoń Szczecin"}
    """

    def __init__(self, queryset):
        self.data = []
        for ts in queryset:
            d = {"team": ts.team.name, "result": self.get_result(ts)}
            d.update(GameSerializer(ts.game).data)
            self.data.append(d)

    def get_result(self, obj):
        """result = models.IntegerField(default=-1, help_text='1 meas won, 0 means draw, 2 means lost , -1 is default')"""
        if obj.result == 1:
            return {"name": "W", "type": "won"}
        elif obj.result == 0:
            return {"name": "R", "type": "draw"}
        elif obj.result == 2:
            return {"name": "P", "type": "lost"}
        else:
            return {"name": None, "type": None}


class CoachGamesAdapter:
    serializer = TeamStatSerializer

    def get(self, coach_id: int, season_name: str = None, limit: int = None):
        print(
            f"data metrics calculation for: coach_id:{coach_id} season:{season_name} with limit: {limit} "
        )
        queryset = (
            TeamStat.objects.all()
            .select_related("game", "game__league", "game__season", "coach")
            .order_by("-game__date")
        )  # values(*self.fileds.keys())
        assert isinstance(
            coach_id, int
        ), f"coach_id need to be type of inteager. it is: {type(coach_id)}"
        queryset = queryset.filter(coach__id=coach_id, game__season__name=season_name)

        print(f"data to calculate: {queryset.count()}")
        if limit is not None:
            queryset = queryset[:limit]
        return self.serializer(queryset).data


class CoachStatSerializer:
    """
    game = models.ForeignKey("Game", on_delete=models.CASCADE, related_name="teamstat")
    team = models.ForeignKey("Team", on_delete=models.CASCADE, related_name="teamstats")
    coach = models.ForeignKey(
        "Coach", on_delete=models.CASCADE, related_name="team_coach_stat", null=True, blank=True
    )
    # calcuable fields
    # auto-calculated fields on save

    result = models.IntegerField(default=-1, help_text='1 meas won, 0 means draw, 2 means lost , -1 is default')
    side = models.IntegerField(default=-1, help_text='0-host, 1-guest -1 error')
    points = models.IntegerField(default=0, help_text='3ptk won, 1ptk draw, 0ptk lost')
    lost_goals = models.IntegerField(default=0)
    gain_goals = models.IntegerField(default=0)
    """

    def _set_default(self, data_storage):
        data_storage["games_played"] = 0
        data_storage["wons"] = 0
        data_storage["draws"] = 0
        data_storage["loses"] = 0
        data_storage["points"] = 0
        data_storage["gain_goals"] = 0
        data_storage["lost_goals"] = 0
        data_storage["avg_goals_losts"] = 0
        data_storage["avg_points"] = 0
        data_storage["avg_goals_gain"] = 0
        data_storage["position_in_table"] = 0
        return data_storage

    def __init__(self, queryset):
        self.data = {
            "total": {},
            "teams": {},
        }
        data = defaultdict(lambda: 0)
        data = self._set_default(data)

        team_data = defaultdict(lambda: dict)

        for q in queryset:
            # Set default values for enconter team.
            team_name = q.team.name
            if not team_data.get(team_name):
                team_data[team_name] = {}
                self._set_default(team_data[team_name])

            data["games_played"] += 1
            team_data[team_name]["games_played"] += 1

            if q.result == 1:
                data["wons"] += 1
                team_data[team_name]["wons"] += 1
            elif q.result == 0:
                data["draws"] += 1
                team_data[team_name]["draws"] += 1
            elif q.result == 2:
                data["loses"] += 1
                team_data[team_name]["loses"] += 1
            team_data[team_name]["points"] += q.points
            team_data[team_name]["lost_goals"] += q.lost_goals
            team_data[team_name]["gain_goals"] += q.gain_goals

            data["points"] += q.points
            data["lost_goals"] += q.lost_goals
            data["gain_goals"] += q.gain_goals

        for team_name, team_meta in team_data.items():
            t = team_meta["games_played"]
            team_meta["avg_goals_gain"] = self.one_digit(team_meta["gain_goals"] / t)
            team_meta["avg_goals_losts"] = self.one_digit(team_meta["lost_goals"] / t)
            team_meta["avg_points"] = self.one_digit(team_meta["points"] / t)

        total = data["games_played"]
        if total != 0:
            data["avg_goals_gain"] = self.one_digit(data["gain_goals"] / total)
            data["avg_goals_losts"] = self.one_digit(data["lost_goals"] / total)
            data["avg_points"] = self.one_digit(data["points"] / total)

        self.data["total"] = dict(data)
        self.data["teams"] = dict(team_data)

    @staticmethod
    def one_digit(number: float) -> float:
        return float("{0:.1f}".format(number))


class CoachCarrierAdapter:
    """Calculates metrics for coach stats for given season."""

    serializer = CoachStatSerializer

    def get(self, coach_id: int, season_name: str = None, limit: int = None):
        print(
            f"# data `season carrier` metrics calculation for: coach_id:{coach_id} season:{season_name} with limit: {limit} "
        )
        queryset = (
            TeamStat.objects.all()
            .select_related("game", "game__league", "game__season", "coach")
            .order_by("-game__date")
        )  # values(*self.fileds.keys())
        assert isinstance(
            coach_id, int
        ), f"coach_id need to be type of inteager. it is: {type(coach_id)}"
        queryset = queryset.filter(coach__id=coach_id, game__season__name=season_name)
        print(f"# data `season carrier` to calculate: {queryset.count()}")
        if limit is not None:
            queryset = queryset[:limit]
        return self.serializer(queryset).data


class CoachCarrierAdapterPercentage(CoachCarrierAdapter):
    def get(self, *args, **kwargs):
        data = super().get(*args, **kwargs)
        return self._percentage(data)

    def _percentage(self, data):
        """Add additional data as percentage represetnation
        for example:

        wons: 2    -->  wons_percentage:  50%
        loses: 1   -->  loses_percentage: 25%
        draws: 1   -->  draws_percentage: 25%
        total: 4
        """
        # We want to calculate percentage values only for total metrics.
        kpis = data["total"]
        total = kpis["games_played"]
        if total != 0:
            kpis["wons_percent"] = 100 * kpis["wons"] / total
            kpis["draws_percent"] = 100 * kpis["draws"] / total
            kpis["loses_percent"] = 100 * kpis["loses"] / total

        else:
            kpis["wons_percent"] = 0
            kpis["draws_percent"] = 0
            kpis["loses_percent"] = 0
        return data


# class CoachStatsAdapter:
#     def get(
#         self,
#         coach_id: str,
#         season: str = None,
#     ):
#         queryset = (
#             Game.objects.all()
#             .select_related("season", "host_coach", "guest_coach", "league")
#             .filter(id=coach_id, season=season)
#             .order_by("date")
#         )
#         excluded_leagues_code = utils.settings.EXCLUDE_LEAGUE_CODES_API
#         if excluded_leagues_code is not None:
#             assert isinstance(
#                 excluded_leagues_code, list
#             ), f"please provide right type of filter for §excluded_leagues_code, should be list we got {type(excluded_leagues_code)}"
#             self.queryset = queryset.exclude(league__code__in=excluded_leagues_code)

#         data = CoachSeasonSerializer().serialize(queryset)
#         self._percentage(data)
#         data["season_name"] = season
#         return data

#     def _percentage(self, data):
#         total = data["games_played"]
#         if total != 0:
#             data["first_percent"] = 100 * data["first_squad_games_played"] / total
#             data["from_bench_percent"] = 100 * data["from_bench"] / total
#             data["bench_percent"] = 100 * data["bench"] / total
#         else:
#             data["first_percent"] = 0
#             data["from_bench_percent"] = 0
#             data["bench_percent"] = 0

#         return data
