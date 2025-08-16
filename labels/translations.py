"""
Label translations for Django's makemessages to find.

This file contains all translatable label strings so Django can 
generate .po files from them.
"""

from django.utils.translation import gettext_lazy as _

# Label descriptions - Django will find these with makemessages
LABEL_DESCRIPTIONS = {
    "Młodzieżowiec": _("Młodzieżowiec"),
    "Bramkarz 185+": _("Bramkarz 185+"),
    "UEFA_PRO": _("UEFA_PRO"),
    "UEFA_A": _("UEFA_A"),
    "Trenerzy przed 30tka": _("Trenerzy przed 30tka"),
    "Trenerzy przed 40tka": _("Trenerzy przed 40tka"),
    "Trener defensywny": _("Trener defensywny"),
    "Trener ofensywny": _("Trener ofensywny"),
    "Partnerzy PlayMaker": _("Partnerzy PlayMaker"),
    "Junior w seniorach": _("Junior w seniorach"),
    "Nie szukam klubu": _("Nie szukam klubu"),
    "Szukam klubu": _("Szukam klubu"),
    "Otwarty na propozycje": _("Otwarty na propozycje"),
    "Spoza UE": _("Spoza UE"),
    "z UE": _("z UE"),
}

# Catalog names - Django will find these with makemessages
CATALOG_NAMES = {
    "Młodzieżowcy": _("Młodzieżowcy"),
    "Wysocy bramkarze": _("Wysocy bramkarze"),
    "Trenerzy profesjonalni": _("Trenerzy profesjonalni"),
    "Trenerzy z UEFA A": _("Trenerzy z UEFA A"),
    "Młodzi trenerzy": _("Młodzi trenerzy"),
    "Spoza UE": _("Spoza UE"),
    "z UE": _("z UE"),
    "Piłkarze otwarci na propozycje": _("Piłkarze otwarci na propozycje"),
    "Piłkarze szukający klubu": _("Piłkarze szukający klubu"),
    "Juniorzy w seniorach": _("Juniorzy w seniorach"),
    "Partnerzy PlayMaker": _("Partnerzy PlayMaker"),
    "Trenerzy ofensywni": _("Trenerzy ofensywni"),
    "Trenerzy defensywni": _("Trenerzy defensywni"),
    "Nie szukam klubu": _("Nie szukam klubu"),
}


def translate_label_description(polish_text: str) -> str:
    """
    Translate label description from database.
    """
    translation_func = LABEL_DESCRIPTIONS.get(polish_text)
    if translation_func:
        return str(translation_func)  # This triggers the actual translation
    return polish_text  # Fallback to original


def translate_catalog_name(polish_text: str) -> str:
    """
    Translate catalog name from database.
    """
    translation_func = CATALOG_NAMES.get(polish_text)
    if translation_func:
        return str(translation_func)  # This triggers the actual translation
    return polish_text  # Fallback to original
