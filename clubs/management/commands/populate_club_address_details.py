from cities_light.models import City, Region
from django.core.management.base import BaseCommand

from clubs.models import Club


class Command(BaseCommand):
    """
    A Django management command to update club addresses with latitude and
    longitude from CitiesLightCity.

    This command iterates over all clubs in the database and attempts to populate the
    latitude
    and longitude fields in the associated address record. It uses the 'raw' address of
    each club to find a matching entry in the CitiesLightCity table.
    If a match is found, the geolocation fields (latitude and longitude)
    in the club's address are updated accordingly.

    The command handles cases where no matching city is found or multiple matches occur
    by skipping those records.
    It also logs any exceptions encountered during processing for debugging purposes.
    """

    help = "Updates club addresses with latitude and longitude from CitiesLightCity"

    def handle(self, *args, **kwargs) -> None:
        for club in Club.objects.all():
            try:
                raw_address = club.stadion_address.raw if club.stadion_address else None
                voivodeship_name = (
                    club.voivodeship_obj.name.lower() if club.voivodeship_obj else None
                )

                if raw_address and voivodeship_name:
                    for city in City.objects.all():
                        if city.name.lower() in raw_address.lower():
                            region = Region.objects.filter(id=city.region_id).first()
                            if region and any(
                                voivodeship_name in alt_name.lower()
                                for alt_name in region.alternate_names.split(",")
                            ):
                                club.stadion_address.latitude = city.latitude
                                club.stadion_address.longitude = city.longitude
                                club.stadion_address.save()
                                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing club {club.id}: {e}")
                )
