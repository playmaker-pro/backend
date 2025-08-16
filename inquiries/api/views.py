import uuid

from django.db.models import ObjectDoesNotExist, QuerySet
from django_fsm import TransitionNotAllowed
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.base_view import EndpointView
from api.errors import NotOwnerOfAnObject
from inquiries.api.serializers import InquiryRequestSerializer, UserInquirySerializer
from inquiries.models import InquiryRequest
from inquiries.services import InquireService
from profiles.services import ProfileService


class InquiresAPIView(EndpointView):
    permission_classes = (IsAuthenticated,)

    def get_my_sent_inquiries(self, request: Request) -> Response:
        """Get all sent inquiries by user"""
        sent_inquiries: QuerySet = InquireService.get_user_sent_inquiries(request.user)
        serializer = InquiryRequestSerializer(
            sent_inquiries, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def get_my_contacts(self, request: Request) -> Response:
        """Get all inquiries contacts by user"""
        contacts: QuerySet = InquireService.get_user_contacts(request.user)
        serializer = InquiryRequestSerializer(
            contacts, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def get_my_received_inquiries(self, request: Request) -> Response:
        """Get all received inquiries by user"""
        InquireService.update_inquiry_read_status_based_on_role(request.user)
        received_inquiries: QuerySet = InquireService.get_user_received_inquiries(
            request.user
        )
        serializer = InquiryRequestSerializer(
            received_inquiries, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def get_my_inquiry_data(self, request: Request) -> Response:
        """Get all received inquiries by user"""
        data = InquireService.get_user_inquiry_metadata(request.user)
        serializer = UserInquirySerializer(data, context=self.get_serializer_context())
        return Response(serializer.data)

    def send_inquiry(
        self, request: Request, recipient_profile_uuid: uuid.UUID
    ) -> Response:
        """Create inquiry request"""
        sender = request.user
        is_anonymous = "anonymous_recipient" in request.data
        try:
            if is_anonymous:
                recipient = ProfileService.get_anonymous_profile_by_uuid(
                    recipient_profile_uuid
                ).user
            else:
                recipient = ProfileService.get_user_by_uuid(recipient_profile_uuid)

            if recipient is request.user:
                raise ValidationError({"error": "You can't send inquiry to yourself"})

        except ObjectDoesNotExist:
            raise NotFound("Recipient does not exist")

        if sender == recipient:
            raise ValidationError({"error": "You can't send inquiry to yourself"})

        body = {
            "anonymous_recipient": is_anonymous,
            "sender": sender.pk,
            "recipient": recipient.pk,
            "recipient_profile_uuid": recipient_profile_uuid,
        }

        serializer = InquiryRequestSerializer(
            data=body, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    def accept_inquiry_request(self, request: Request, request_id: int) -> Response:
        """Accept inquiry request by id"""
        try:
            inquiry_object = InquiryRequest.objects.get(pk=request_id)
        except ObjectDoesNotExist:
            raise NotFound("InquiryRequest does not exist")

        if inquiry_object.recipient != request.user:
            raise NotOwnerOfAnObject

        try:
            serializer = InquiryRequestSerializer(
                instance=inquiry_object, context=self.get_serializer_context()
            ).accept()
        except TransitionNotAllowed:
            raise ValidationError("You can't accept this request")

        return Response(serializer.data, status=status.HTTP_200_OK)

    def reject_inquiry_request(self, request: Request, request_id: int) -> Response:
        """Reject inquiry request by id"""
        try:
            inquiry_object = InquiryRequest.objects.get(pk=request_id)
        except ObjectDoesNotExist:
            raise NotFound("InquiryRequest does not exist")

        if inquiry_object.recipient != request.user:
            raise NotOwnerOfAnObject

        try:
            serializer = InquiryRequestSerializer(
                inquiry_object, context=self.get_serializer_context()
            ).reject()
        except TransitionNotAllowed:
            raise ValidationError("You can't reject this request")

        return Response(serializer.data, status=status.HTTP_200_OK)
