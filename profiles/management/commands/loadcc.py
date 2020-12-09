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
        if param == 'Wszystko do uzgodnienia, jestem otwarty na propozycje :D':
            return 500
        if param =="50-60":
            return 60
        if param == '999':
            return 500
        if param =='100km':
            return 100
        if param =='15km' or param =="Max 15km":
            return 15
        if param =="61a":
            return 61
        if param =="50, przy lepszej lidze więcej":
            return 50
        if param =='0-20 Max':
            return 20
        if param =='100km+':
            return 100
        if param =='Możliwa przeprowadzka' or param =="Nawet przeprowadzka":
            return 500
        if param =="---":
            return None
        if param == "1000":
            return 500
        if param == "Zależnie od poziomu klubu":
            return None
        if param =="10000" or param =="10000" or param =="1000km" or param =="Dowolnie ":
            return 500
        if param =='15-35':
            return 35
        if param =='200km' or param =='200 km':
            return 200
        if param =='50-150':
            return 150
        if param =="6 kilometrów":
            return 6
        if param == "100/120":
            return 120
        if param =='400 km' or param == '400km':
            return 400
        if param =="20-30km" or param =="20-30 km":
            return 30
        if param == "10-20 km":
            return 20
        if param =="15-20":
            return 20
        if param =="Do 50 km":
            return 50
        if param =="30km od miejsca zamieszkania":
            return 30
        if param == "30/40":
            return 40
        if param == "Odległość nieokreślona":
            return None
        if param =="1111":
            return 500
        if param =="30-35":
            return 35
        if param =="obojętnie" or param == "Nie gra roli" or param =="Dowolna" or param =="Nie ma znaczenia" or param =="Bez limitu" or param =="500+" or param =="Cała Polska" or param =="Dowolnie" or param =="niema ruznicy":
            return 500
        if param =="Aksamitna 20" or param =="Nie wiem" or param =="Opatówko 28" or param =="Kętrzyńskiego 107/8" or param == "Osiedle Robotnicze 85/2" or param =="Dębieczna 58" or param =="Autobusy w obrębie okolic Poznania":
            return None
        if param == "5-6":
            return 6
        if param =="30,40":
            return 40
        if param == "50km (możliwość zmiany miejsca zamieszkania na terenie 2 grupy III ligi)":
            return 50
        if param == "Nowa 25/1" or param =="Nagietkowa 3" or param == "Skarbka 2/45" or param =="Skalista 20" or param =="Sokoła 40" or param == "Ul. Akacjowa 8D/3":
            return None
        if param =="50/60 km":
            return 60
        if param =="50a":
            return 50
        if param =="1k":
            return 1
        if param =="100 km (Bez problemowa możliwość zmiany miejsca zamieszkania z pomocą klubu)" or param =="100km, możliwość przeprowadzki":
            return 100
        if param =="do 30km":
            return 30
        if param == "50-60":
            return 60
        if param =="80km":
            return 80
        if param =="Zależy":
            return None
        if param == "Nie chce":
            return 0
        if param =="Zbąszyńska 1" or param == "Andersa 178" or param =="Kornela Makuszyńskiego 21" or param =="Chorzowska  11" or param =="Mickiewicza 70" or param == "Ul.plac 1-go Maja 3/1" or param == "11-Go Listopada 2 /28" or param =="Plac Grunwaldzki" or param =="Bohaterów Modlina 22/15" or param =="Szaflika 10": 
            return None
        if param =="Bez różnicy wszędzie dojadę " or param =="nieokreślone" or param =="Nie ma różnicy" or param == "jestem otwarty na propozycje" or param =="odległość nie ma dla mnie znaczenia" or param =="bez znaczenia" or param =="w razie potrzeby moge zmienci miejsce zamieszkania" or param =="Bez ograniczeń" or param =="bez różnicy" or param == "Jestem w stanie zmienić miejsce zamieszkania" or param =="600 (możliwa przeprowadzka)":
            return 500
        if param =="Koszalińska 64E/5" or param == "Turkusowa 26" or param =="Aleksandry Śląskiej" or param =='W zależności od klubu' or param == 'Słopnice 1050'  or param =='Kamienna 5/1' or param == "Nie jestem w stanie określić" or param == "Mickiewicza 95/6" or param =="Brzozowa 1":
            return None
        if param =="70km" or param == "70 km":
            return 70
        if param =='30 km' or param =='30km':
            return 30
        if param =="300km" or param =='300 km':
            return 300
        if param =='100km' or param =='100 km' or param =="100 /możliwość przeprowadzki":
            return 100
        if param == "130km":
            return 130
        if param == '60km' or param =='60 km':
            return 60
        if param =='Os. Zachód B1D 15':
            return None
        if param is None or param == '' or param == '-':
            return None
        if param =='250 km maks':
            return 250
        if param =="70-100km, w zależności od oferty jestem w stanie rozważyć dalsze wyjazdy lub przeprowadzkę":
            return 100
        if param =='100-150km':
            return 150
        if param =="Bez różnicy" or param == 'Wszędzie' or param == 'obojętnie' or param == 'Odległość nieokreślona ' or param == 'bez znaczenia' or param =='nie ma znaczenia' or param =='dowolna odległość km':
            return 500
        if param == "Internat?":
            return None
        if param == "Centrum":
            return None
        if param == '100+':
            return 100
        if param == '5km':
            return 5
        if (param.startswith('50 ') and param.endswith('ie')) or param =='50 km' or param == '50km': #== '50 bądź mieszkać w bursie' or param  =='50 bądź mieszkać w bursie':
            return 50
        if param =='Błogosław 8 ' or param == 'Horbaczewskiego 25':
            return 8
        if param =='cała polska':
            return 500
        if param == "Mölnesjön gatan 35":
            return None
        if param == 'O':
            return 0
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
        elif param.lower() == 'pomocnik - defensywny (6)':
            return 5
        elif param.lower() == 'pomocnik - środkowy (8)':
            return 6
        elif param.lower() == 'pomocnik - ofensywny (10)':
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
        from clubs.models import Club, Team
        with open(options['path'], newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for i, row in enumerate(reader):
                # if i < 335:
                #     continue
                # print(row['address2'])
                # continue
                self.stdout.write(self.style.SUCCESS(pprint.pprint(row)))
                
            
                first_name = row['Imie_wprowadzajacego']
                last_name = row['Nazwisko_wprowadzajacego']
                
                email = 'matiszumi94@gmail.com'
                # email = row['Email_wprowadzajacego']
                # if email == '':
                #     print(f'>>>>> skip: {first_name}, {last_name}')
                #     continue
                
                initial_password = 'amd!0s#k4d9ciasd'

                
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                        user = User.objects.create_user(
                            email=email.lower(),
                            first_name=first_name,
                            last_name=last_name,
                            password=initial_password,
                            declared_role='T',
                        )
                c,_ = Club.objects.get_or_create(name=row['Nazwa_druzyny'])
                t,_ = Team.objects.get_or_create(club=c, name=row['Nazwa_druzyny'])
                t.manager = user
                t.save()
                phone = row['Telefon_wprowadzajacego']
                profile = user.profile
                profile.phone = phone
                profile.save()
                break
             
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