from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint

User = get_user_model()


class Command(BaseCommand):
    help = 'Load dumped profiles from csv file.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
        parser.add_argument('type', type=str)

    def prefered_leg_map(self, param):
        if param == 'Lewa':
            return 1
        elif param == 'Prawa':
            return 2
        else:
            return None
        
    def player_soccer_goals_map(self, param):
        '''     
        Mapowanie
        "Ekstraklasa" lub "1 liga" lub "2 liga" lub "Centralna Liga Juniorów" lub "Makroregionalna Liga Juniorów" => "Poziom profesjonalny"
        "3 liga" lub "1 liga wojewódzka" => "Poziom półprofesjonalny"
        Pozostałe => "Poziom regionalny"
        '''
        if param in ["Ekstraklasa", "1 liga", "2 liga", "Centralna Liga Juniorów", "Makroregionalna Liga Juniorów"]:
            return 1
        elif param in ["3 liga", "1 liga wojewódzka"]:
            return 2
        elif param is not None:
            return 3
        else:
            return None

    def training_ready_map(self, param):
        '''6 lub więcej treningów
        4 lub 5 treningów
            TRAINING_READY_CHOCIES = (
        (1, '1-2 treningi'),
        (2, '3-4 treningi'),
        (3, '5-6 treningi')
         )
        '''
        if '1' in param or '2' in param:
            return 1
        elif '3' in param or '4' in param:
            return 2
        elif '5' in param or '6' in param:
            return 3
        return None

    def card_map(self, param):
        '''
            CARD_CHOICES = (
        (1, 'Mam kartę na ręku'),
        (2, 'Nie wiem czy mam kartę na ręku'),
        (3, 'Nie mam karty na ręku')
        )
        '''
        if param == 'Mam kartę na ręku':
            return 1
        elif param == 'Nie wiem czy mam kartę na ręku':
            return 2
        elif param == 'Nie mam karty na ręku':
            return 3
        else:
            return None

    def transfer_status_map(self, param):
        '''
            TRANSFER_STATUS_CHOICES = (
        (1, 'Szukam klubu'),
        (2, 'Rozważę wszelkie oferty'),
        (3, 'Nie szukam klubu')
    )
            Mapowanie
        "Zostawiam CV na przyszłość" lub "Otwarty na propozycje" => "Rozważę wszelkie oferty"
        "Szukam klubu" => "Szukam klubu"
        "Nie chcę zmieniać klubu" => "Nie szukam klubu"
        '''
        if param == 'Zostawiam CV na przyszłość' or param == 'Otwarty na propozycje':
            return 2
        elif param == 'Szukam klubu':
            return 1
        elif param == 'Nie chcę zmieniać klubu':
            return 3
        else:
            return None
    def practice_distance_map(self, param):
        '''
        jeśli pojawia się znak inny niż liczbowy, to wyznaczamy wartość na podstawie cyfr przed tym znakiem, tzn:
        "100/" => 100
        "100 km / 200" => 100
        '''
        if param is None:
            return None

        try:
            pram_int = int(param)
            return param_int
        except:
            param = param.replace('km', '')
            param = param.replace('  ', ' ')
            params = param.split('/')
            try:
                param_int = params[0]
                return param_int
            except:
                return None
        
    def birth_map(self, param):
        '''
        'birth', '2003-10-15T22:00:00Z'
        '''
        if param is None:
            return None
        return param[:10]

    def position_map(self, param, leg):
        '''
        W bazie wix jest Obrońca - boczny. Dopasowanie prawy / lewy jest w przypadku
        position = "Obrońca boczny" & foot = "Prawa" => "Obrońca Prawy"
        position = "Obrońca boczny" & foot = "Lewa" => "Obrońca Lewy"

        POSITION_CHOICES = [
            (1, 'Bramkarz'),
            (2, 'Obrońca Lewy'),
            (3, 'Obrońca Prawy'),
            (4, 'Obrońca Środkowy'),
            (5, 'Pomocnik defensywny (6)'),
            (6, 'Pomocnik środkowy (8)'),
            (7, 'Pomocnik ofensywny (10)'),
            (8, 'Skrzydłowy'),
            (9, 'Napastnik'),
        ]
        '''
        if param is None:
            return None
        if param == 'Obrońca boczny' and leg == 'Lewa':
            return 2
        elif param == 'Obrońca boczny' and leg == 'Prawa':
            return 3
        elif param.lower() == 'obrońca - środkowy':
            return 4
        elif param.lower() == 'bramkarz':
            return 1
        elif param.lower() == 'pomocnik defensywny (6)':
            return 5
        elif param.lower() == 'pomocnik środkowy (8)':
            return 6
        elif param.lower() == 'pomocnik ofensywny (10)':
            return 7
        elif param.lower() == 'skrzydłowy':
            return 8
        elif param.lower() == 'npastnik':
            return 9
        else:
            return None

    def phone_map(self, param):
        if param is None:
            return None
        if len(param) == 9:
            return '+48'+param
        if param.startswith('+') and len(param) == 12:
            return param

    def get_param_or_none(self, row, param_name):
        return row[param_name] if row[param_name] != '' else None

    def handle(self, *args, **options):
        role = options['type']
        with open(options['path'], newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.stdout.write(self.style.SUCCESS(pprint.pprint(row)))
                email = row['wix_id']
                first_name = row['name']
                last_name = row['surname']
                initial_password = '123!@#qweQWE'
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        password=initial_password,
                        declared_role=role,
                    )
        
                practice_distance = self.get_param_or_none(row, 'address2')
                phone = self.get_param_or_none(row, 'contact_telephone')
                card = self.get_param_or_none(row, 'club_card')
                formation = self.get_param_or_none(row, 'formation')
                formation_alt = self.get_param_or_none(row, 'alternative_formation')
                laczynaspilka_url = self.get_param_or_none(row, 'LNP_profile')
                facebook_url = self.get_param_or_none(row, 'contact_facebook')
                height = self.get_param_or_none(row, 'high')
                weight = self.get_param_or_none(row, 'weight')
                123!@#qweQWE = self.get_param_or_none(row, 'wix_id')
                prefered_leg = self.get_param_or_none(row, 'foot')
                birth_date = self.get_param_or_none(row, 'birth')
                about = self.get_param_or_none(row, 'about_me')
                soccer_goal = self.get_param_or_none(row, 'league_goal_new')
                training_ready = self.get_param_or_none(row, 'training_new')
                position_raw = self.get_param_or_none(row, 'position')
                position_raw_alt = self.get_param_or_none(row, 'alternative_position')
                transfer_status = self.get_param_or_none(row, 'transfer_status')
                motivation1 = self.get_param_or_none(row, 'motivation1')
                motivation2 = self.get_param_or_none(row, 'motivation2')
                motivation3 = self.get_param_or_none(row, 'motivation3')
                motivation_other = self.get_param_or_none(row, 'motivation_other')
                self.stdout.write(self.style.SUCCESS(f'{user} added.'))
                
                club = self.get_param_or_none(row, 'club')
                active_pznpn = self.get_param_or_none(row, 'active_PZPN')
                idlnp = self.get_param_or_none(row, 'ID_LNP')
                region = self.get_param_or_none(row, 'region')
                team_club_league_voivodeship_ver = f'{club} activePZPN:{active_pznpn} IDLNP:{idlnp} {region}  {wix_id}'
  

                try:
                    player = Player.objects.get(wix_id=wix_id)
                    mapper_id = player.id
                except Player.DoesNotExist:
                    mapper_id = None

                profile = user.profile

                profile.data_mapper_id = mapper_id
                profile.height = height
                motivation = ''
                if motivation1 is not None or motivation2 is not None or motivation3 is not None or motivation_other is not None:
                    if about is None:
                        about = ''
                    motivation = '\n\nMotywacja:\n'
                    if motivation1 is not None:
                        motivation += motivation1
                    if motivation2 is not None:
                        motivation += f'\n{motivation2}'
                    if motivation3 is not None:
                        motivation += f'\n{motivation3}'
                    if motivation_other is not None:
                        motivation += f'\n{motivation_other}'
                if about is None and motivation == '':
                    about = None
                else:
                    about = about + motivation
                profile.country = 'PL'
                profile.training_ready = self.transfer_status_map(training_ready)
                profile.practice_distance = self.practice_distance_map(practice_distance)
                profile.facebook_url = facebook_url
                profile.phone = self.phone_map(phone)
                profile.formation = formation
                profile.formation_alt = formation_alt
                profile.card = self.card_map(card)
                profile.laczynaspilka_url = laczynaspilka_url
                profile.about = about
                profile.transfer_status = self.transfer_status_map(transfer_status)
                profile.prefered_leg = self.prefered_leg_map(prefered_leg)
                profile.weight = weight
                profile.birth_date = self.birth_map(birth_date)
                profile.position_raw = self.position_map(position_raw, prefered_leg)
                profile.position_raw_alt = self.position_map(position_raw_alt, prefered_leg)
                profile.soccer_goal = self.player_soccer_goals_map(soccer_goal)
                profile.team_club_league_voivodeship_ver = team_club_league_voivodeship_ver
                profile.save()
                if wix_id is not None:
                    user.verify(silent=True)
                    user.save()
                    # profile.save()
                self.stdout.write(self.style.SUCCESS(f'{user.profile} updated.'))
                # print(row)
                
                
        # user = User.objects.create_user(username='john',
        #                          email='jlennon@beatles.com',
        #                          password='glass onion')
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

            # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))