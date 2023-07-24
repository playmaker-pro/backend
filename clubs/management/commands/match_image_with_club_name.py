import json
import os
import re
from unidecode import unidecode

from clubs.models import Club
from django.core.management import BaseCommand
from .utils import get_club_without_img, PATH_TO_FILE, PATH_TO_FLAGS


class Command(BaseCommand):
    def handle(self, *args: any, **options: any) -> any:
        """Match clubs name with herb file names"""

        clubs = Club.objects.exclude(teams=None)
        clubs_dict = get_club_without_img(clubs)

        re_pattern = "^\d\."

        club_pic_names = [
            {re.sub(re_pattern, "", file.split(".jpg")[0]).lower().strip(): file}
            for file in os.listdir(PATH_TO_FLAGS)
            if os.path.isfile(os.path.join(PATH_TO_FLAGS, file))
        ]

        clubs_without_pic = {}
        clubs_with_pic = 0

        clubs_without_pic_matched = {}

        for key, values in clubs_dict.items():

            name = unidecode(values["name"])
            name_length = len(name.split(" "))
            url = values["picture"]

            if not url:
                # Check if club dont have picture url

                clubs_without_pic[key] = values

                for file in club_pic_names:

                    file_name = list(file.keys())[0]
                    file_whole_name = list(file.values())[0]

                    if file_name in name.lower() or name.lower() in file_name:
                        # if file name == club name from base, break loop
                        # print(f'1: {file_name}, 2:{name.lower()}')

                        clubs_without_pic_matched[key] = {
                            "club_name": name,
                            "pic_name": file_name,
                            "file_name": file_whole_name,
                        }

                        break

                    file_name_splitted = file_name.split(" ")
                    len_file_name = len(file_name)

                    if len_file_name in range(name_length, name_length + 2):
                        # check if length of file name is in range club name length plus + (to exclude words like
                        # LKS/KS/TS). Probably there are clubs in base which wont have this word in name.

                        if len_file_name >= 2:

                            for element in file_name_splitted:
                                if element in name.lower() and len(element) >= 4:
                                    # check if word from list isnt a short word like LKS/TS/GKS. If true, break loop

                                    clubs_without_pic_matched[key] = {
                                        "club_name": name,
                                        "pic_name": file_name,
                                        "file_name": file_whole_name,
                                    }
                                    break

            elif url:
                clubs_with_pic += 1

        with open(PATH_TO_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(clubs_without_pic_matched))
