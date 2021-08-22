from data.models import TeamStat

from stats import utilites as utils


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
        return {
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
        code = obj.game.league.code
        name = obj.game.league.name
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
    '''
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
    '''
    def __init__(self, queryset):
        self.data = []
        for ts in queryset:
            d = {
                "result": self.get_result(ts)
            }
            d.update(GameSerializer(ts.game))
            self.data .append(d)

    def get_result(self, obj):
        """result = models.IntegerField(default=-1, help_text='1 meas won, 0 means draw, 2 means lost , -1 is default')"""
        if obj.result == 1:
            return {'name': 'W', 'type': 'won'} 
        elif obj.result == 0:
            return {'name': 'R', 'type': 'draw'} 
        elif obj.result == 2:
            return {'name': 'P', 'type': 'lost'}
        else:
            return {'name': None, 'type': None}


class CoachGamesAdapter:
    fields = None

    def get(self, coach_id: int, season: str = None, limit: int = None):
        queryset = (
            TeamStat.objects.all()
            .select_related("game", "game__league", "game__season", "coach")
            .order_by("-game__date")
        )  # values(*self.fileds.keys())

        queryset = queryset.filter(coach__id=coach_id, game__season__name=season)

        if limit is not None:
            queryset = queryset[:limit]
        return TeamStatSerializer(queryset).data

# class CoachStatsAdapter:
#     """

#     Uses data.PlayerStat

#     1. know how to get data from data.models
#     2. know how to filter qs
#     3. know how to strucrure it
#     4.. .knows too much......

#     single player stats (player groupped)
#     Season performance + latest games
#     """

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
