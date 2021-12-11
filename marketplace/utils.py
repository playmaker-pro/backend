from django.utils import timezone


def get_datetime_from_year(year):
    if not year:
        return None
    return timezone.datetime(year, 1, 1)
