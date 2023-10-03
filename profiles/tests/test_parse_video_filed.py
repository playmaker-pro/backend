from django.test import TestCase

from profiles.utils import extract_video_id
from utils import testutils as utils

utils.silence_explamation_mark()


class ParseVideoUrl(TestCase):
    def setUp(self):
        self.urls = [
            ("https://youtu.be/k6apIuEmwnk", "k6apIuEmwnk"),
            ("https://youtu.be/jFRn1DB5cn4", "jFRn1DB5cn4"),
            ("https://www.youtube.com/watch?v=rknQ2ZNYGy8", "rknQ2ZNYGy8"),
            (
                "https://megawrzuta.pl/download/472a2702739bf081c9f0c18a97245339.html",
                None,
            ),
            ("https://www.youtube.com/watch?v=b6dCIiPHXyA", "b6dCIiPHXyA"),
            ("https://www.youtube.com/watch?v=Bfdcp3RKBLY", "Bfdcp3RKBLY"),
            ("https://www.youtube.com/watch?v=LUDGej8kja8", "LUDGej8kja8"),
            ("https://youtu.be/fLe2XHeeIWw", "fLe2XHeeIWw"),
            ("https://youtu.be/GnmvwUi0Nrg", "GnmvwUi0Nrg"),
            ("https://youtu.be/7OW2cfv-2Bw", "7OW2cfv-2Bw"),
            ("https://youtu.be/44CAh6Eum7w", "44CAh6Eum7w"),
            ("https://m.youtube.com/watch?v=WdnTytj75bc", "WdnTytj75bc"),
            (
                "https://www.youtube.com/watch?v=zwrtBhYoCL8&feature=youtu.be&ab_channel=qevprodbm",  # noqa: E501
                "zwrtBhYoCL8",
            ),
        ]

    def test_parse_youtube_id_from_given_url(self):
        for url, result in self.urls:
            assert extract_video_id(url) == result
