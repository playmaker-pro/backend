import json

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext

from followers import forms
from followers.models import Item, Pin
from followers.pin_managers import manager


def trending(request):
    """
    The most popular items
    """
    # if not request.user.is_authenticated:
    #     # hack to log you in automatically for the demo app
    #     admin_user = authenticate(username='admin', password='admin')
    #     auth_login(request, admin_user)

    # show a few items

    popular = Item.objects.all()[:50]

    response = render(request, "core/trending.html", {"popular": popular})
    return response


@login_required
def feed(request):
    """
    Items pinned by the people you follow
    """
    context = {}
    feed = manager.get_feeds(request.user.id)["normal"]
    if request.GET.get("delete"):
        feed.delete()
    activities = list(feed[:25])
    if request.GET.get("raise"):
        raise RuntimeError(activities)
    context["feed_pins"] = enrich_activities(activities)
    response = render(request, "core/feed.html", context)
    return response


@login_required
def aggregated_feed(request):
    """
    Items pinned by the people you follow
    """
    context = {}
    feed = manager.get_feeds(request.user.id)["aggregated"]
    if request.GET.get("delete"):
        feed.delete()
    activities = list(feed[:25])
    if request.GET.get("raise"):
        raise RuntimeError(activities)
    context["feed_pins"] = enrich_aggregated_activities(activities)
    response = render(request, "core/aggregated_feed.html", context)
    return response


def profile(request, id):
    """
    Shows the users profile
    """
    profile_user = get_user_model().objects.get(id=id)
    feed = manager.get_user_feed(profile_user.id)
    if request.GET.get("delete"):
        feed.delete()
    activities = list(feed[:25])
    context = {}
    context["profile_user"] = profile_user
    context["profile_pins"] = enrich_activities(activities)
    response = render(request, "core/profile.html", context)
    return response


@login_required
def pin(request):
    """
    Simple view to handle (re) pinning an item
    """
    output = {}
    if request.method == "POST":
        data = request.POST.copy()
        data["user"] = request.user.id
        form = forms.PinForm(data=data)

        if form.is_valid():
            pin = form.save()
            if pin:
                output["pin"] = dict(id=pin.id)
            if not request.GET.get("ajax"):
                return redirect_to_next(request)
        else:
            output["errors"] = dict(form.errors.items())

    else:
        form = forms.PinForm()

    return render_output(output)


def redirect_to_next(request):
    return HttpResponseRedirect(request.GET.get("next", "/"))


def render_output(output):
    ajax_response = HttpResponse(json.dumps(output), content_type="application/json")
    return ajax_response


@login_required
def follow(request):
    """
    A view to follow other users
    """
    output = {}
    if request.method == "POST":
        data = request.POST.copy()
        data["user"] = request.user.id
        form = forms.FollowForm(data=data)

        if form.is_valid():
            follow = form.save()
            if follow:
                output["follow"] = dict(id=follow.id)
        else:
            output["errors"] = dict(form.errors.items())
    else:
        form = forms.FollowForm()
    return HttpResponse(json.dumps(output), content_type="application/json")


def enrich_activities(activities):
    """
    Load the models attached to these activities
    (Normally this would hit a caching layer like memcached or redis)
    """
    pin_ids = [a.object_id for a in activities]
    pin_dict = Pin.objects.in_bulk(pin_ids)
    for a in activities:
        a.pin = pin_dict.get(a.object_id)
    return activities


def enrich_aggregated_activities(aggregated_activities):
    """
    Load the models attached to these aggregated activities
    (Normally this would hit a caching layer like memcached or redis)
    """
    pin_ids = []
    for aggregated_activity in aggregated_activities:
        for activity in aggregated_activity.activities:
            pin_ids.append(activity.object_id)

    pin_dict = Pin.objects.in_bulk(pin_ids)
    for aggregated_activity in aggregated_activities:
        for activity in aggregated_activity.activities:
            activity.pin = pin_dict.get(activity.object_id)
    return aggregated_activities
