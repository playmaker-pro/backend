import json
import logging

from django.core.mail import send_mail, mail_managers
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import TestFormSerializer

from products.models import Product, Request
from users.models import User

from .decorators import is_owner

logger = logging.getLogger(__name__)


class TestFormAPIView(generics.CreateAPIView, generics.UpdateAPIView):

    serializer_class = TestFormSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post', 'patch']
    model = Request
    queryset = Request.objects.all()

    def perform_create(self, serializer):
        return serializer.save()

    def post(self, request, *args, **kwargs):

        data = request.data

        name = 'Wsparcie transferowe dla piłkarza'
        product = get_object_or_404(Product, title=name)
        user = get_object_or_404(User, pk=data['user'])

        data = {
            'product': product.id,
            'user': user.id,
            'raw_body':
                {
                    'city': data['city'],
                    'leagues': data['leagues'],
                    'distance': data['distance'],
                }
        }

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        new_data = self.perform_create(serializer)

        try:
            message = serializer.data
            subject = f'User {user.username} requested help'
            mail_managers(subject, json.dumps(message))

        except Exception as e:
            logger.error(f'Mail could not be sent')

        return Response({'success': new_data.id}, status=status.HTTP_201_CREATED)

    @is_owner(query=queryset)
    def patch(self, request, *args, **kwargs):

        request_help = get_object_or_404(self.queryset, id=kwargs.get('pk'))
        data = request_help.raw_body

        request.data.pop('user')

        data['videos'] = request.data.get('videos')
        data['comment'] = request.data.get('comment')

        request.data['raw_body'] = data
        self.partial_update(request, *args, **kwargs)

        try:
            message = data
            subject = f'Request update: {request_help.user}'
            mail_managers(subject, json.dumps(message))

        except Exception as e:
            logger.error(f'Mail could not be sent')

        return Response({'success': 'Successfully updated'}, status=status.HTTP_201_CREATED)
