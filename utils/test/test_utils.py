from contextlib import contextmanager

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.db.models import signals
from factory.django import mute_signals

from clubs.models import Season
from utils import testutils as utils

utils.silence_explamation_mark()


class GetCurrentSeasonTest(TestCase):
    """
    JJ:
    Definicja aktualnego sezonu
    (wyznaczamy go za pomocą:
        jeśli miesiąc daty systemowej jest >= 7
        to pokaż sezon (aktualny rok/ aktualny rok + 1).
        Jeśli < 7 th (aktualny rok - 1 / aktualny rok)
    """

    def setUp(self) -> None:
        settings.SEASON_DEFINITION["middle"] = 7

    def test_season_assign(self):
        tdatas = (
            ((2020, 7, 1), "2020/2021"),
            ((2020, 6, 20), "2019/2020"),
            ((2020, 12, 31), "2020/2021"),
        )
        for date_settings, result in tdatas:
            date = timezone.datetime(*date_settings)
            assert (
                Season.define_current_season(date) == result
            ), f"Input data:{date_settings} date={date}"


@contextmanager
def mute_post_save_signal():
    """Mute post save signal. We don't want to test it in some cases."""
    with mute_signals(signals.post_save):
        yield
