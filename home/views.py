from django.http import Http404
from django.shortcuts import render


def players_base(request):  # @todo to be removed

    return render(request, 'home/list_player.html', {'items': [1,2,3,4]})