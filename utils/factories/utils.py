import datetime
import os
import random

from faker import Faker

from voivodeships.models import Voivodeships

fake: Faker = Faker()


def get_stub_path(stub_filename: str) -> str:
    """Create abs path for file inside stub's directory"""
    dir_name = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_name, f"stubs/{stub_filename}")


def get_random_voivo() -> Voivodeships:
    """Get random voivodeship"""
    return Voivodeships.objects.all().order_by("?").first()


def get_random_int(_min: int, _max: int) -> int:
    """Get random int on range"""
    return fake.random_int(min=_min, max=_max)


def get_random_date(start_date: str, end_date: str) -> datetime.date:
    """Get random date on range"""
    return fake.date_between(start_date=start_date, end_date=end_date)


def get_random_phone_number() -> str:
    """Get random phone number with Polish pattern"""
    return fake.numerify(text="###-###-###")


def get_random_address() -> str:
    """Get random address with street"""
    return fake.address().replace("\n", ", ")


def get_random_bool() -> int:
    """Get random bool value (0, 1)"""
    return random.getrandbits(1)
