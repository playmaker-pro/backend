import os
from typing import Union

from clubs.models import Club, Team
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from functools import reduce
from django.db.models import Q

LEAGUES = [
    "Ekstraklasa",
    "1 Liga",
    "2 Liga",
    "3 Liga",
    "4 Liga",
    "5 Liga",
    "Klasa Okręgowa",
    "A Klasa",
    "B Klasa",
]

PATH_TO_LOG = os.path.dirname(__file__)
PATH_TO_FILE = os.path.join(PATH_TO_LOG, "result_herbs.txt")

PATH_TO_FLAGS = rf"/home/playmakerpro/Herby/renamed"


def get_club_without_img(clubs: Club, herbs: bool = False) -> Union[list, dict]:
    """Return clubs without herbs"""

    clubs_dict = {}
    herbs_list = []

    for club in clubs:
        for team in club.teams.all():
            if (
                team.league
                and team.league.highest_parent
                and team.league.highest_parent.name in LEAGUES
            ):
                if herbs:
                    herbs_list.append(
                        {
                            "name": club.name,
                            "picture": True if club.picture else None,
                            "club_id": club.id,
                            "voivodeship": club.voivodeship.name
                            if club.voivodeship
                            else None,
                            "team_name": [
                                (team, team.league.highest_parent.name)
                                for team in club.teams.all()
                            ],
                        }
                    )
                    break

                clubs_dict[club.id] = {
                    "name": club.name,
                    "picture": club.picture.url if club.picture else None,
                    "team_name": team.name,
                    "team_league": team.league.highest_parent.name,
                }
                break

    if herbs:
        return herbs_list

    return clubs_dict


def change_club_image(clubs: Club, clubs_matched: dict) -> None:

    for club in clubs:
        club_id = str(club.id)

        if clubs_matched.get(club_id) and not club.picture:

            try:
                file_name = clubs_matched[club_id]["file_name"]
                club.picture.save(
                    file_name, File(open(PATH_TO_FLAGS + file_name, "rb"))
                )

            except ObjectDoesNotExist:
                pass


def modify_name(obj: Union[Team, Club]) -> str:
    excluded_parts = ['AKS', 'SPK', 'AZS', 'WKS', 'KP', 'KS', 'BKS', 'GKS', 'GLKS', 'KKS', 'Tkkf', 'Uokp',
                      'FC', 'LKS', 'MLKS', 'KTS-K', 'MUKS', 'AKS','OKS', 'TS', 'JUN', 'MKP', 'HKS', 'Tlks',
                      'ZKS', 'I', 'II', 'III', 'Mmks', 'KLUB', 'SPORTOWY', 'PIŁKARSKI', 'ROBOTNICZY', 'SKS', 'RKS',
                      'ŁKS', 'MKS', 'AFC', 'MOS', 'OSIR', 'BKP', 'GTS', 'DKS', 'DTS', 'FKS', 'GKP', 'ZLKS', 'Gmlks',
                      'ZGKS', 'MGKS', 'MGHKS', 'GTS', 'Mgks', 'Luks', 'Glzs', 'Glkr', 'LKP', 'Mglks', 'Klks',
                      'Stowarzyszenie', 'LZS', 'UKS', 'GRANIT', 'LGKS', 'CHKS', 'ŁKP', 'GSS', 'UMKS', 'CKS', 'Mosir', 'Mksr',
                      'Mbks','Plks', 'SL', 'AMSPN', 'Amspn', 'SKP', 'Guks', 'KSS', 'Uplks', 'APN', 'AP', 'TKS', 'GAS',
                      'GZS', 'ZS', 'STS', 'PTS', 'AF', 'PKS', 'TP', 'KRS', 'NKS', 'Osppn', 'SMP', 'LGKS', 'Skfkp',
                      'SSR', 'SS', 'Smpn', 'Swmp', 'TMS', 'goksir', 'Granit', 'SR', 'Sapn', 'Otps', 'Mgts', 'Ksgc',
                      'Goldengranit', 'Kkpk', 'Mzlks', 'KKP', 'Aspn', 'ŚKS', 'PSS', 'RTS', 'SKF', 'Zlks', 'MTS','KOS',
                      'SFC', 'Mguks', 'Smks', 'ZKS', 'Kkpn', 'Pwks', 'Mluks', 'OSP', 'Orkan', 'Glkst', 'Chks']

    words_to_remove = ['Agrotex', 'Stihl','WSS', '37', '1910', 'K', 'JUN', 'Enea',
                       'Spółka', 'Akcyjna', 'Sportowe', 'Mmks', 'Muks', 'SSA', 'SPZ', 'OO',
                       'Piłkarski', 'Brax', 'TON', 'Gminny', 'Ludowy', '38', 'Z', 'A', 'P', '1917', 'CEZ', 'AMSPN',
                       'Az-bud', 'Wg-skałka', 'ZSP', 'WAMAG', 'Foto', 'Higiena', 'Gealan', 'N-w-ch', 'WOY',
                       '„konfeks”', 'Filsport', '&', 'Pwsz', 'Jelcz', 'Gmina', 'Srwsio','ZA',
                       'Wamag', 'FMS', 'SA', 'ECO', 'Video', 'MAX', 'ROL', 'DLN', 'San-bud', 'Miejsko-gminny', 'N',
                       'Ino', 'Mal', 'W', 'Tir', 'J-aw', 'FA', 'Fair', 'Pol',  'ATB', 'SP', 'Gtstir',
                       'Osiedlowy', 'TG', 'IKS','EBE', 'SHR', 'KLB', 'CUP', 'S', 'Smwsir', 'Geyer&hosaja',
                       'TAN', 'Towsportowe', 'Ar-tig', 'L', 'GAZ', 'ZEM', 'Steico', 'Elektrobut', 'Kombud',
                       'Farmutil', 'VSB', 'Polomarket', 'Mitex', 'SC', 'Fundacja', 'MK', 'Mal-bud']
    words_to_replace = {
        'Uczniowski Ludowy Klub Sportowy': 'ULKS',
        'Stowarzyszenie Sportowo - Edukacyjne Petrus IM KS Henryka Bagińskiego Przy Parafii ŚW AP Piotra Pawła W Łapach': 'Petrus Łapy',
        'Fundacja Sportu Dzieci Akademia Malucha Akademia Młodego Piłkarza Białystok': 'Akademia Malucha Białystok',
        'Jarosławskie Stowarzyszenie Rozwoju Regionalnego W Jarosławiu': 'JKS Jarosław',
        'Stowarzyszenie Szkółka Piłkarska Gminy Lipce Reymontowskie': 'Lipce Reymontowskie',
        'Akademia Piłkarskich Talentów Brylant Włodzimierz Pawluczuk': 'APT Brylant Bielsk Podlaski',
        'Gminna Akademia Piłkarska Gminy Dębica Chemik Pustków':'Gapg Dębica Chemik Pustków',
        'Klub Sportowy Stowarzyszenie Piłkarskie Widzew Łódź': 'Kssp Widzew Łódź',
        'MKS Limanovia W Limanowej': 'Limanovia Limanowa',
        'KS Brochów (Wrocław)': 'KS Brochów',
        'Bocheński Klub Sportowy': 'BKS Bochnia',
        'Konstantynowska Akademia Sport': 'KAS Konstantynów',
        'mechanik brzezina': 'Mechanik Brzezina',
        'Budowlany KS Bydgoszcz': 'BKS Bydgoszcz',
        'Międzypokoleniowy KP Powiat Pilski Piła': 'MKP Piła',
        'Miejsko Gminny Uczniowski Klub Sportowy': 'Mguks',
        'Międzyzakładowy Klub Sportowy': 'MKS',
        'POM Iskra Piotrowice': 'Iskra Piotrowice',
        'MKS Tęcza Krosno Odrz': 'Tęcza Krosno Odrzańskie',
        'Mlksvictoria Sulejówek': 'MLKS Victoria Sulejówek',
        'LKS Sokół W Popowie': 'Sokół Popów',
        'BKS Bobrzanie Bolesławiec': 'BKS Bolesławiec',
        'Sportis SFC Łochowo': 'Sportis Łochowo',
        'Mrks Czechowice-dziedzice': 'Mrks Czechowice-Dziedzice',
        'Zbąszynecka Akademia Piłkarska':'ZAP Zbąszynek',
        'Koluszkowski Klub Sportowy Koluszki': 'KKS Koluszki',
        'Łosicki DOM Kultury': 'ŁDK Łosice',
        'Uczniowski LKS': 'ULKS',
        'Błękitn ': 'Błękitni',
        'SAN': 'San',
        'DAR': 'Dar',
        'LEW': 'Lew',
        'TUR': 'Tur',
        'ŁĘK': 'Łęk',
        'SÓL': 'Sól',
        'Kobiecy KP': 'KKP',
        'GKS - Zarzecze': 'GKS Zarzecze',
        'Babicha': 'LKS Babicha',
        'Bemowska Szkoła Sport': 'BSS',
        'Kobiecy Klub Piłki Nożnej': 'Kkpn',
        'Mazurski Klub Sportowy': 'MKS',
        'Akademicki Związek Sportowy': 'AZS',
        'Młodzieżowy Ludowy Klub Sportowy': 'MLKS',
        'Stowarzyszenie KLB Sportowytrzciana': 'SKS Trzciana',
        'Ostrołęcka Akademia Piłki Nożnej Ostrołęka': 'APN Ostrołęka',
        'Młodzieżowy Klub Sportowy Zaborze Z Siedzibą W Zabrzu': 'Mks Zaborze',
        'Gminny Ośrodek Szkolenia Dzieci Młodzieży': 'Gosdim',
        'Międzyszkolne Gminne Towarzystwo Sportowe': 'Mgts',
        'Szkółka Piłkarska Soccer Ropczyce': 'SP Soccer Ropczyce',
        'Luks Radłovia Radłów Miejsko Gminna Akademia Sportu W Radłowie': 'Radłovia Radłów',
        'Fundacja Akademii Sportu Gryf': 'Akademia Sportu Gryf',
        'Grodziskie Towarzystwo Sportowe Grodzisk Mazowiecki': 'GTS Grodzisk Mazowiecki',
        'Stowarzyszenie Szkółka Piłkarska Borekkraków': 'SP Borek Kraków',
        'Bieruńska Akademia Piłkarska': 'BAP',
        'Wieluński Klub Sportowy W Wieluniu': 'WKS Wieluń',
        'Płońska Akademia Futbolu': 'AF Płońsk',
        'Ludowy Klub Sportowyodrzechowa': 'Ludowy Klub Sportowy Odrzechowa',
        'Dziewczęca APN': 'DAPN',
        'Młodzieżowy Klub Sportowy': 'MKS',
        'Sopocka Akademia Piłkarska': 'SAP Sopot',
        'Włocławska Akademia Piłkarska': 'WAP',
        'Dziecięca Akademia Piłkarska W Dębicy': 'DAP Dębica',
        'LKS Sokół Dąbrówka Wlkp': 'Sokół Dąbrówka Wielkopolska',
        'Dziecięca Akademia Piłkarska' : 'DAP',
        'Gminna Akademia Piłkarska': 'GAP',
        'RKP SP ROW W Rybniku': 'ROW Rybnik',
        'KS LZS Gryf Piaseczno KS Skarpa': 'Gryf Piaseczno',
        'Iskra Góra ŚW Małgorzaty': 'Iskra Góra Świętej Małgorzaty',
        'Ludowy Klub Sportowy Korona W Lgocie': 'LKS Korona Lgota',
        'Arbiter Tęczowy LAS Pizza & Pasta Olsztyn': 'Arbiter Olsztyn',
        'Ludowy Klub Sportowyraba Książnice': 'Ludowy Klub Sportowy Raba Książnice',
        'Stowsportumłodz': 'SSM',
        'Gminny Ludowwy KS Lelis': 'GLKS Lelis',
        'Akademia Piłki Nożnej': 'APN',
        'POM': 'pomorskie',
        'Podl ': 'Podlaski',
        'Zakładowy Klub Sportowy': 'ZKS',
        'W-W': 'Wrocław',
        'Iks': 'LKS',
        'DĄB': 'Dąb',
        'GAĆ': 'Gać',
        'LUB': 'Lubelski',
        'Kulturalny Klub Sportowy': 'KKS',
        'Uczniowski Młodzieżowy Klub Sportowy':'UMKS',
        'Kaliski Klub Sportowy': 'KKS',
        'Miejski Klub Sportowy Znicz W Pruszkowie': 'Znicz Pruszków',
        'Miejski Klub Sportowy': 'MKS',
        'KS Polonia Środa Wlkp': 'Polonia Środa Wielkopolska',
        'Wlkp': 'Wielkopolski',
        'Łaskarzewski Klub Sportowy': 'ŁKS',
        'Gdański Klub Sportowy Gedania': 'Gedania Gdańsk',
        'Robotniczy Klub Sportowy Garbarnia Kraków': 'Garbarnia Kraków',
        'Tomaszowskie Centrum Sportu': 'Lechia Tomaszów Mazowiecki',
        'ŚW ': 'Świętokrzyski',
        'Klub Sportowy Wisłoka': 'Wisłoka Dębica',
        'MKS Podlasie Biała Podlaska': 'Podlasie Biała Podlaska',
        'LKS Polonia Łódź - Andrzejów': 'Polonia Andrzejów',
        'KS Ursus': 'Ursus Warszawa',
        'Akad Piłk': 'AP',
        'Akademia Piłkarska': 'AP',
        'Ludowy Klub Sportowy': 'LKS',
        'LG': 'Lotos Gdańsk',
        'Beniaminek Starogard GD': 'Beniaminek Starogard Gdański',
        'W-wy': 'Warszawy',
        'Bobowa Bobowa': 'KS Bobowa',
        'Akademia Piłk ': 'AP ',
        'Akademia Piłk': 'AP',
        'Akademia Futbolu': 'AF',
        'Amatorski KS': 'AKS',
        'ŚWI': 'Świdwin',
        'Akademia Sportu': 'AS',
        'Alternatywny Klub Sportowy': 'AKS',
        'Ciechanowieckie Stowarzyszenie Piłkarskie Unia': 'CSP Unia Ciechanowiec',
        'Cieszyński Klub Sportowy Piast': 'CKS Piast Cieszyn',
        'Dęblińska Szkoła Piłkarska UKS Orlik Dęblin': 'UKS Orlik Dęblin',
        'GKS Gietrzwałd-unieszewo': 'GKS Gietrzwałd',
        'Gminny Klub Sportowy': 'GKS',
        'W-wa': 'Warszawa',
        'Wm-sport': 'Escola Varsovia',
        'M-gks': 'Mgks',
        'Gminny Ośrodek Sportu Rekreacji Novi-rzezawianka': 'Gosir Novi Rzezawianka',
        'Miejski Górniczo-hutniczy Klub Sportowy Bolesław W Bukownie': 'MGHKS Bolesław Bukowno',
        'GZ LZS W Łubnianach': 'LZS Łubniany',
        'FC Chronstau - Chrząstowice': 'FC Chronstau Chrząstowice',
        'Fundacja Kujawsko-pomorskich Akademii Piłkarskich JSS Toruń': 'JSS Toruń',
        'Miejsko-gminny Klub Sportowy': 'MGKS',
        'Towarzystwo Sportowe': 'TS',
        'Gminno-uczniowski Klub Sportowy Gorzkowice': 'Guks Gorzkowice',
        'K-koźle': 'Kędzierzyn-Koźle',
        'KS Pro- Wietlin': 'KS Wietlin',
        'Glks-t Agrosport Leśna Podl': 'Glks-t Agrosport Leśna Podlaska',
        'UKS FA Fair-play Złotów': 'UKS Złotów',
        'Międzyszkolny Uczniowski Klub Sportowy': 'MUKS',
        'Gminny Młodzieżowy KS': 'GMKS',
        'U- Bytów': 'Bytów',
        'LZS Kolbark-błyskawica Kolbark': 'LZS Kolbark',
        'Ludowy Zespół Sportowy': 'LZS',
        'Wiejskie Towarzystwo Kulturalno-sportowe ': 'WTKS',
        'M-glks': 'Mglks',
        'Uczniowski Klub Sportowy': 'UKS',
        'LKS Perła Szczaki - Złotokłos': 'Perła Złotokłos',
        'BTS Rekord': 'Rekord Bielsko-Biała',
        ' - ': '-',
        'pomorskie': 'Pomorskie',
        'RYŚ': 'Ryś',
        'ŁĘG': 'Łęg',
        'BÓR': 'Bór',
        'Toruńska Akademia Futsalu': 'TAF',
        'ŚW' : 'Świętokrzyski',
        'MŁP': 'Małopolski',
        'Klub Sportowy': 'KS',
        'KS Gmchełmża Cyklon Kończewice': 'Chełmża Cyklon Kończewice',
        'Międzygminny Klub Sportowy': 'MGKS',
        'Glks-t': 'GLKS',
        'Miejski Uczniowski Klub Sportowy': 'MUKS',
        'Klub Piłkarski': 'KP',
        'Stowarzyszenie Przyjaciół Regulic Nieporazu Regulice': 'Sprin Regulice',
        'MAZ': 'Mazowiecki',
        'Klub Sportowy Vulcan Wólka ML': 'Vulcan Wólka Mlądzka',
        'Gminna Akademia Sportu': 'GAS',
        'Fundacja GES Sport Academy Poznań': 'GES Sport Academy Poznań',
        'Łódzki Klub Sportowy': 'ŁKS Łódź',
        'Indywidualna Szkoła Futbolu': 'ISF',
        'Lot-balice': 'Lot Balice',
        'ŚL': 'Śląskie',
        'Niemieckie Towarzystwo Szkolne W Warszawie': 'NTS Warszawa',
        'Akademia Kreatywnego Futbolu': 'AKF',
        'Fundacja Bydgoskiej Szkółki Piłkarskiej Jacademy Bydgoszcz':'Jacademy Bydgoszcz',
        'Akademia Młodego Piłkarza': 'AMP',
        'Uczniowski Klub Piłkarski': 'UKS',
        'Akademia Kobiecego Futbolu': 'AKF',
        'Stowarzyszenie Sportowe': 'SS',
        'Stowarzyszenie Klub Sportowy': 'SKS',
        'Szkoła Mistrzostwa Sportowego': 'SMS',
        'Dziecięca Szkółka PN': 'DSPN',
        'Stowarzyszenie Klutury Fizycznej': 'SKF',
        'Tryb': 'Trybunalski ',
        'Stowarzyszenie Zjednoczonego Klubu Sportowego Parafialnego Amicus Mórka': 'Amicus Mórka',
        'Szkółka Piłkarska Junior Kalisz Pomorski': 'Junior Kalisz Pomorski',
        'Zaczernie': 'KS Zaczernie',
        'Fabr': 'Fabryczny',
        'Śledziejowice Śledziejowice': 'LKS Śledziejowice',
        'Blks Granit Bychawa': 'Granit Bychawa',
        'NAD': 'nad',
        'Iławski Klub Sportowy Jeziorak Iława': 'Jeziorak Iława',
        'Mareckie Inwestycje Miejskie': 'Marcovia Marki',
        'Rylowa': 'Rylovia Rylowa',
        'LKS Plon Garbatka-letnisko': 'Plon Garbatka-Letnisko',
        'LKS Wisła Główina-sobowo': 'LKS Wisła Główina-Sobowo',
        'LKS Czarni Kalinów-kalinowice': 'Czarni Kalinów-Kalinowice',
        'Ruch Popkowice-zadworze': 'Ruch Popkowice-Zadworze',
        'BUK': 'Buk',
        'LAS': 'Las',
        'Rudołtowice-ćwiklice': 'Rudołtowice-Ćwiklice',
        'LKS Babia Góra Koszarawa': 'Koszarawa Babia Góra',
        'LKS WEL Lidzbark Welski': 'Wel Lidzbark',
        'Rywal-klon': 'Rywal-Klon',
        'Grądy-malerzowice': 'Grądy-Malerzowice',
        'RÓJ': 'Rój',
        'Porajów-kopaczów': 'Porajów-Kopaczów'
    }
    excluded_strings = ['Bielsko-Biała', 'Busko-zdrój', 'Bruk-bet', 'Kędzierzyn-Koźle', 'Golub-dobrzyń', 'Soccer-calcio',
                        'Start-Regent', 'Kruszyna-prędocin', 'Hat-trick', 'Szklarska-Poręba', 'GKS-Zarzecze', 'Pub-gol',
                        'Tymon-tymowa', 'Popkowice-Zadworze', 'Kalinów-kalinowice', 'Główina-sobowo', 'Garbatka-Letnisko',
                        'Kalinów-Kalinowice', 'Rudołtowice-Ćwiklice', 'Rywal-Klon', 'Psary-Babienica', 'Porajów-Kopaczów',
                        'Juna-trans']

    name_to_modify = obj.name
    club_name = obj.club.name if isinstance(obj, Team) else name_to_modify

    """
    Replace the words in the given club_name with their corresponding replacements, 
    which can be used to create shortcuts for common prefixes or phrases.
    """
    club_name = reduce(lambda s, kv: s.replace(*kv), words_to_replace.items(), club_name)

    """
    Remove common unnecessary phrases specified in words_to_remove from club_name 
    and join the remaining words into a new modified club name."
    """
    club_name = ' '.join([w for w in club_name.split() if w not in words_to_remove])
    modified_club_name = club_name

    """
    Rearrange and modify the given club name by moving certain excluded parts (e.g. common sport club prefixes) 
    to the beginning of the name and removing any duplicate or unnecessary words. 
    Specifically, this code checks if any excluded part is present in the club name and, if so, 
    moves it to the front of the name while maintaining the order of the other words. 
    It also removes any duplicates and ensures that only unique words remain in the final modified club name.
    """
    parts = modified_club_name.split('-')
    if len(parts) > 1 and not any(exclude in modified_club_name for exclude in excluded_strings):
        _, *rest_parts = parts[1].split()
        modified_club_name = f"{parts[0]} {' '.join(rest_parts)}"

    split_modified_club_name = modified_club_name.split()
    for part in excluded_parts:
        if part in split_modified_club_name:
            part_index = split_modified_club_name.index(part)
            modified_club_name = ' '.join(
                [*split_modified_club_name[part_index:],
                 *split_modified_club_name[:part_index]]
            )
        else:
            modified_club_name = ' '.join(split_modified_club_name)

        split_modified_club_name = modified_club_name.split()
        if len(split_modified_club_name) > 2:
            if part in split_modified_club_name:
                split_modified_club_name.remove(part)

        unique_words = []
        for w in split_modified_club_name:
            if w not in unique_words:
                unique_words.append(w)
        modified_club_name = ' '.join(unique_words)

    """ 
        Check if all teams assigned to the given Club object play in the Futsal league. 
        If they do, modify the Club's name to indicate that it is a Futsal club by appending 
        the string "(Futsal)" to the Club name.
        """
    if isinstance(obj, Club):
        teams = obj.teams.all()
        futsal_leagues = ['Futsal', 'PLF']
        query = Q()
        for league in futsal_leagues:
            query |= Q(historical__league_history__league__highest_parent__name__contains=league)

        if teams.filter(query).distinct().count() == teams.count():
            if 'Futsal' not in club_name:
                modified_club_name = modified_club_name + ' (Futsal)'

    """
    Extracts the team number from the given team name, if it includes a Roman numeral from I to IV. 
    This helps distinguish teams within a club that share a similar name.
    """
    team_number = next((part for part in name_to_modify.split() if part in ['I', 'II', 'III', 'IV']), '')

    """
    Add a suffix to a team name indicating that the team is playing in a futsal league if the team's 
    club is not defined as a futsal club and the team is playing in a futsal league.
    """
    if isinstance(obj, Team) and not all(
            'Futsal' in team.team_name_with_current_league or 'PLF' in team.team_name_with_current_league for team in
            obj.club.teams.all() if team.team_name_with_current_league):
        team_number = '(Futsal)' if any(
            league_name in obj.team_name_with_current_league for league_name in ['Futsal', 'PLF']
        ) and 'Futsal' not in obj.club.name else team_number

    modified_name = modified_club_name + " " + team_number if team_number else modified_club_name

    return modified_name
