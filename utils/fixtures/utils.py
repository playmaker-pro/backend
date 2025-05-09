import datetime
import random

from faker import Faker

from voivodeships.models import Voivodeships

fake = Faker(locale="pl_PL")


def get_random_int(min_val: int, max_val: int) -> int:
    """Generate a random integer within the given range."""
    return random.randint(min_val, max_val)


def get_random_date(start_date: str = "-50y", end_date: str = "-15y") -> datetime.date:
    """Generate a random date within the given range."""
    return fake.date_between(start_date=start_date, end_date=end_date)


def get_random_bool() -> bool:
    """Generate a random boolean value."""
    return random.choice([True, False])


def get_random_voivo():
    """Get a random voivodeship object."""

    return Voivodeships.objects.order_by("?").first()
