from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, mail_managers
from django.conf import settings

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TestFormSerializer

from products.models import Product, Request
from users.models import User


class TestFormAPIView(APIView):

    serializer_class = TestFormSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request):

        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)
        data = data.data

        name = 'Wsparcie transferowe dla piłkarza'
        product, _ = Product.objects.get_or_create(
            title=name
        )

        try:
            user = User.objects.get(pk=data['user'])

            data = {
                'product': product,
                'user': user,
                'raw_body':
                    {
                        'city': data['city'],
                        'leagues': data['leagues'],
                        'distance': data['distance'],
                    }
            }

            Request.objects.create(**data)

            message = f'Requested: Wsparcie transferowe'
            subject = f'User {user.username} requested help'

            mail_managers(subject, message)

            return Response({'success': 'form sent'}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:

            return Response({'error': 'Form not sent. Data is not valid'}, status=status.HTTP_400_BAD_REQUEST)

