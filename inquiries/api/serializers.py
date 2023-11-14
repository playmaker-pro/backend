from django.contrib.auth import get_user_model
from rest_framework import serializers

from inquiries import models as _models
from users.api.serializers import BaseUserDataSerializer

User = get_user_model()


class InquiryRequestSerializer(serializers.ModelSerializer):
    sender_object = BaseUserDataSerializer(read_only=True, source="sender")
    recipient_object = BaseUserDataSerializer(read_only=True, source="recipient")

    class Meta:
        model = _models.InquiryRequest
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        """Validate if user can make request"""
        if not self.instance:
            sender: User = attrs.get("sender")
            recipient: User = attrs.get("recipient")
            userinquiry: _models.UserInquiry = sender.userinquiry

            if not userinquiry.can_make_request:
                raise serializers.ValidationError(
                    f"You have reached your limit of inquiries ({userinquiry.counter}/{userinquiry.limit})."
                )

            if _models.InquiryRequest.objects.filter(
                sender=sender, recipient=recipient
            ).exists():
                raise serializers.ValidationError(
                    f"You have already sent inquiry to {recipient}."
                )

            if cross_request := _models.InquiryRequest.objects.filter(
                sender=recipient, recipient=sender
            ).first():
                if cross_request.status in _models.InquiryRequest.RESOLVED_STATES:
                    raise serializers.ValidationError(
                        f"This user has already replied to your request (status={cross_request.status})."
                    )
                self._accept_cross_request(cross_request)

        return attrs

    def _accept_cross_request(
        self, cross_request: _models.InquiryRequest
    ) -> "InquiryRequestSerializer":
        """
        Cross request is case when user A send request to user B
        when user B already sent request to user A.
        We want to auto-accept this kind of request and avoid creating new one.
        """
        return InquiryRequestSerializer(cross_request).accept()

    def accept(self) -> "InquiryRequestSerializer":
        """Accept inquiry request"""
        self.instance.accept()
        self.instance.save()
        return self

    def reject(self) -> "InquiryRequestSerializer":
        """Reject inquiry request"""
        self.instance.reject()
        self.instance.save()
        return self


class InquiryPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = _models.InquiryPlan
        exclude = ("sort",)


class InquiryContactSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="_email", allow_null=True)

    class Meta:
        model = _models.InquiryContact
        fields = (
            "phone",
            "email",
        )


class UserInquiryLogSerializer(serializers.ModelSerializer):
    message_type = serializers.CharField(source="message.message_type", read_only=True)
    body = serializers.SerializerMethodField(
        method_name="get_log_message", read_only=True
    )

    class Meta:
        model = _models.UserInquiryLog
        fields = ("created_at", "message_type", "body")

    def get_log_message(self, obj: _models.UserInquiryLog) -> str:
        """Get message body with user related data"""
        return obj.log_message_body


class UserInquirySerializer(serializers.ModelSerializer):
    plan = InquiryPlanSerializer(read_only=True)
    contact = InquiryContactSerializer(source="user.inquiry_contact", read_only=True)
    logs = UserInquiryLogSerializer(many=True, read_only=True)

    class Meta:
        model = _models.UserInquiry
        fields = "__all__"
