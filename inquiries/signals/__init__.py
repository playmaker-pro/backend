from django.dispatch import Signal

inquiry_sent = Signal()
inquiry_accepted = Signal()
inquiry_rejected = Signal()
