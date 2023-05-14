from contextlib import contextmanager
from factory.django import mute_signals
from django.db.models import signals


@contextmanager
def mute_post_save_signal():
    """Mute post save signal. We don't want to test it in some cases."""
    with mute_signals(signals.post_save):
        yield
