from typing import Dict

import factory
from django.contrib.auth import get_user_model

from features.models import AccessPermission, FeatureElement, Feature
from roles.definitions import PROFILE_TYPE_SHORT_MAP

User = get_user_model()


def create_default_permissions() -> Dict[str, bool]:
    permission_map: dict = PROFILE_TYPE_SHORT_MAP
    return {key: False for key in permission_map.keys()}


class AccessPermissionFactory(factory.django.DjangoModelFactory):
    """Factory for AccessPermission model""" ""

    class Meta:
        model = AccessPermission

    access = "all"


class FeatureElementFactory(factory.django.DjangoModelFactory):
    """Factory for FeatureElement model"""

    class Meta:
        model = FeatureElement

    name = factory.Faker("name")
    permissions = create_default_permissions()

    @factory.post_generation
    def create_access_permissions(self, create, extracted, **kwargs):
        """Because access permission is ManyToMany field, we have to fill it manually"""
        if not create:
            return
        if not self.access_permissions.exists():
            elements = AccessPermissionFactory.create()
            self.access_permissions.set([elements])


class FeatureFactory(factory.django.DjangoModelFactory):
    """Factory for Feature model"""

    class Meta:
        model = Feature

    name = factory.Faker("name")
    enabled = True
    keyname = factory.Faker("name")

    @factory.post_generation
    def create_elements(self, create, extracted, **kwargs):
        """Because elements is ManyToMany field, we have to fill it manually"""
        if not create:
            return

        if not self.elements.exists():
            elements = FeatureElementFactory.create()
            self.elements.set([elements])
