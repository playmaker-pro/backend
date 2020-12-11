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
        #arser.add_argument('off', type=str)

    def get_param_or_none(self, row, param_name):
        return row[param_name] if row[param_name] != '' else None

    def handle(self, *args, **options):
        
        with open(options['path'], newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            for i, row in enumerate(reader):
                # if i < 335:
                #     continue
                # print(row['address2'])
                # continue
                self.stdout.write(self.style.SUCCESS(pprint.pprint(row)))
                print(f"{row['wix_id']}----{row['coaches_coopertion']}")
                # if options['off'] == 'T':
                #     email = 'jacek.jasinski8@gmail.com'
                # else:
                #     email = row['wix_id']
                #     if email == '':
                #         continue

                # try:
                #     user = User.objects.get(email=email)
                # except User.DoesNotExist:
                #     continue
                
                # prefered_leg = self.get_param_or_none(row, 'foot')
                # position_raw = self.get_param_or_none(row, 'position')
                # position_raw_alt = self.get_param_or_none(row, 'alternative_position')
                
                # profile = user.profile
                
                           
                # profile.position_raw = self.position_map(position_raw, prefered_leg)
                # profile.position_raw_alt = self.position_map(position_raw_alt, prefered_leg)

                # user.profile.save(silent=True)
                # if options['off'] == 'T':
                #     break
                
                
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