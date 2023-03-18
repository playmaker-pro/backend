from typing import Dict, Any
from django.core.management.base import BaseCommand
from profiles.models import PlayerProfile, CoachProfile, ScoutProfile, ManagerProfile
from clubs.models import Club, Team, LeagueHistory
from external_links.utils import create_or_update_player_external_links


class Command(BaseCommand):
    help = 'Update or create external links for specified profile type'

    def add_arguments(self, parser) -> None:
        parser.add_argument('profile_type', type=str, help='The type of profile to update or create external links for')

    def handle(self, *args, **options: Dict[str, Any]) -> None:
        """
        This method updates or creates ExternalLink objects for a specified profile type. It first checks if the
        specified profile_type is valid by comparing it to a list of allowed types. If it is not valid, an error
        message is printed and the method exits. Otherwise, the method creates a mapping between the profile_type and
        the corresponding model. It then retrieves all objects of that model and iterates through them, calling the
        create_or_update_player_external_links function. This function updates or creates ExternalLink object for a
        given profile by collecting all external links from the profile instance and adding them to the corresponding
        ExternalLinksEntity. If the profile has no existing external links, the create_or_update_player_external_links
        function will still create an empty ExternalLink object, which can later be updated with new links if necessary.
        Finally, a success message is printed to the console.
        """
        profile_type = options.get('profile_type', '').lower()
        valid_types = ['player', 'coach', 'scout', 'manager', 'club', 'team', 'league']

        if profile_type not in valid_types:
            self.stdout.write(self.style.ERROR(f"Invalid profile type: {profile_type}"))
            return

        model_mapping = {
            'player': PlayerProfile,
            'coach': CoachProfile,
            'scout': ScoutProfile,
            'manager': ManagerProfile,
            'club': Club,
            'team': Team,
            'league': LeagueHistory
        }

        model = model_mapping[profile_type]
        profiles = model.objects.all()

        for profile in profiles:
            create_or_update_player_external_links(profile)

        self.stdout.write(
            self.style.SUCCESS(f"External links for {len(profiles)} {profile_type}s created successfully.")
        )
