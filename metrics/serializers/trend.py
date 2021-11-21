

class TrendSerializer:
    @classmethod
    def serialize(cls, game, team_name):
        return game.is_winning_team(team_name)
