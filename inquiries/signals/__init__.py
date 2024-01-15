from django.dispatch import Signal

inquiry_sent = Signal()
inquiry_accepted = Signal()
inquiry_rejected = Signal()
inquiry_pool_exhausted = Signal()
inquiry_restored = Signal()
inquiry_reminder = Signal()
