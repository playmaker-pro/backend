from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from users.models import User


def is_owner(query):
    def wrap_func(func):
        def wrapper_func(request, *args, **kwargs):
            """ check if request user is owner of request object """

            user = request.request.data.get('user')

            user = get_object_or_404(User, id=int(user))
            request_data = query.filter(id=kwargs.get('pk'), user=user)

            if request_data.exists():
                return func(request, *args, **kwargs)

            else:
                return Response(
                    {'error': 'User is not owner of this request'},
                    status=status.HTTP_403_FORBIDDEN
                )

        return wrapper_func

    return wrap_func
