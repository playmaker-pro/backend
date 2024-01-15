# Deprecation : @dep -2 due to pandas
# from django.core.management.base import BaseCommand

# from profiles.utils import match_player_videos


# class Command(BaseCommand):
#     """
#     Match players with their videos based on data from csv file
#     """

#     def add_arguments(self, parser) -> None:
#         parser.add_argument(
#             "csv_file",
#             type=str,
#             help="Path to the CSV file to import player videos from",
#         )

#     def handle(self, *args, **kwargs) -> None:
#         """
#         Expects the csv_file to have the following columns:
#             player - the user id,
#             url - the URL of the video,
#             title - the title of the video,
#             description - the description of the video.

#         For each row, the method retrieves the PlayerProfile object that corresponds to the player
#         value of the current row and then creates a new PlayerVideo object with the values from
#         the current row, or updates an existing one if it already exists. If the PlayerVideo
#         object was created, a message is printed indicating the creation of the object.
#         If it already existed, a message is printed indicating that the object already exists.
#         """
#         csv_file = kwargs["csv_file"]
#         match_player_videos(csv_file)
