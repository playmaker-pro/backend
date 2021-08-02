from data.models import TeamStat, Team
from rest_framework.serializers import ModelSerializer
from django.db.models import Avg, Count, Min, Sum
from clubs.models import League
from clubs.models import Team as CTeam


class TeamStatSerializer:
    @classmethod
    def calc(cls, teamstat):
        return {
            "result": teamstat.result,
            "side": teamstat.side,
            "points": teamstat.points,
            "lost_goals": teamstat.lost_goals,
            "gain_goals": teamstat.gain_goals,
            # "game": teamstat.game.date,
            # "league_code": teamstat.game.league.code,
            # "league_name": teamstat.game.league.name,
        }

class LeagueMatches:
    def serialize(self):
        pass


class TeamMetrics:
    def serialize(self, team_name, season_name, league_code):
        total = TeamStat.objects.filter(
            team__name=team_name,
            game__season__name=season_name,
            game__league__code=league_code,
        ).order_by(
            '-game__date'
        )

        points = total.aggregate(Sum('points'))
        gain_goals = total.aggregate(Sum('gain_goals'))
        lost_goals = total.aggregate(Sum('lost_goals'))
        wons = total.filter(result=1)

        losts = total.filter(result=2) 
        total_count = total.count()
        wons_count = wons.count()
        losts_count = losts.count()
        trend = total[:5]
        '''
            {
                "position": "1",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Manchaster",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "P", "P", "R"],
            },
        '''
        trends = []
        for t in trend:
            if t.result == 1:
                trd = 'W'
            elif t.result == 2:
                trd = 'P'
            elif t.result == 0:
                trd = 'R'
            trends.append(trd)
        output = {
            'team': team_name,
            'games': total_count,
            'wins': wons_count,
            'losts': losts_count,
            'draws': total_count - wons_count - losts_count,
            'points': points['points__sum'],
            'goals': f"{gain_goals['gain_goals__sum']}:{lost_goals['lost_goals__sum']}",
            'trend': trends,
        }

        return output



from data.models import Game

class GameSerializer:
    '''

    host_team = 
    guest_team = 
    host_score = models.IntegerField(null=True)
    host_coach = models.ForeignKe
    host_team_name = models.TextField()
    guest_score = models.IntegerField(null=True)
    guest_coach = models.Foreign
    guest_team_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
            {
                "name": "Kolejka 30",
                "games": [
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Sokół I",
                        "guest": "Lechia Dzierżoniów",
                        "score": "2 - 1",
                        "date": "10.05 21:00",
                    },
    '''
    @classmethod
    def calc(cls, game, host_picture, guest_picture):
        from easy_thumbnails.files import get_thumbnailer

        # thumbnailer = get_thumbnailer('animals/aardvark.jpg')

        # thumbnail_options = {'crop': True}
        # for size in (50, 100, 250):
        #     thumbnail_options.update({'size': (size, size)})
        #     thumbnailer.get_thumbnail(thumbnail_options)

        # # or to get a thumbnail by alias
        # thumbnailer['large']
        try:
            
            host_pic = get_thumbnailer(host_picture)['nav_avatar']
        except:
            host_pic = ''
        try:
            guest_pic = get_thumbnailer(guest_picture)['nav_avatar']
        except:
            guest_pic = ''

        return {
            'guest_pic': guest_pic,
            'host_pic': host_pic,
            'date': game.date,
            'score': f'{game.host_score} - {game.guest_score}',
            'host': game.host_team_name,
            'guest': game.guest_team_name,
            'url': game.league._url,
        }

from collections import defaultdict

class LeagueMatchesMetrics:
    def serialize(self, league, season_name):
        matches = Game.objects.filter(
            league__name__icontains=league.name,
            season__name=season_name,
            league__code=league.code,
            
        ).order_by('-date')
        output = defaultdict(list)
        for game in matches:
            q = game.queue
            try:
                
                host_pic = CTeam.objects.get(name__icontains=game.host_team_name)
            except:
                host_pic = ''
            try:
                guest_pic = CTeam.objects.get(name__icontains=game.guest_team_name)
            except:
                guest_pic = ''
            output[q].append(GameSerializer.calc(game, host_pic, guest_pic))
        return output
