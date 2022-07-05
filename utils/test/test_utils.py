import logging
from datetime import datetime

import mock
import pytest
from django.test import TestCase
from django.utils import timezone
from profiles import models
from profiles.utils import get_current_season
from roles import definitions
from users.models import User
from utils import testutils as utils


utils.silence_explamation_mark()


class GetCurrentSeasonTest(TestCase):
    """
    JJ:
    Definicja aktualnego sezonu
    (wyznaczamy go za pomocą:
        jeśli miesiąc daty systemowej jest >= 7 to pokaż sezon (aktualny rok/ aktualny rok + 1).
        Jeśli < 7 th (aktualny rok - 1 / aktualny rok)
    """

    def test_season_assign(self):
        tdatas = (
            ((2020, 7, 1), "2020/2021"),
            ((2020, 6, 20), "2019/2020"),
            ((2020, 12, 31), "2020/2021"),
        )
        for date_settings, result in tdatas:
            date = timezone.datetime(*date_settings)
            assert get_current_season(date) == result
