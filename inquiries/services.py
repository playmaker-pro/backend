from .models import InquiryRequest


def unseen_requests(queryset, user):
    return queryset.filter(recipient=user, status__in=InquiryRequest.UNSEEN_STATES)


def unseen_user_requests(user):
    return InquiryRequest.objects.filter(
        recipient=user, status=InquiryRequest.STATUS_SENT
    )


def update_requests_with_read_status(queryset, user):
    for request in queryset.filter(status=InquiryRequest.STATUS_SENT):
        if request.recipient == user:
            request.read()
            request.save()
