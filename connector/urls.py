
class URL:

    BASE = "http://localhost:8000/"

    # List of team histories
    # TeamHistoryMongoRepo().all()
    TEAM_HISTORIES = BASE + "th/"

    # Every plays that team participate in
    # TablesMongoRepo().filter({"rows.team.id": team_id})
    TEAM_PLAYS = BASE + "get-team-plays/{team_id}/"

    # Every team that participate in given play
    # TablesMongoRepo().find_or_none({"play.id": play_id})
    PLAY_TEAMS = BASE + "get-play-teams/{play_id}/"

    # Club details
    # ClubsMongoRepo().find_or_none({"id": club_id})
    CLUB_DETAILS = BASE + "club-details/{club_id}/"

    # List of leagues
    # LeagueMongoRepo().all()
    LEAUGES = BASE + "leagues/"
