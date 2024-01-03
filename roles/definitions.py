from dataclasses import dataclass
from enum import Enum
from typing import List

PLAYER_SHORT, PLAYER_FULL = "P", "Piłkarz"
COACH_SHORT, COACH_FULL = "T", "Trener"
CLUB_SHORT, CLUB_FULL = "C", "Działacz klubu"
MANAGER_SHORT, MANAGER_FULL = "M", "Menadżer"
SCOUT_SHORT, SCOUT_FULL = "S", "Skaut"
GUEST_SHORT, GUEST_FULL = "G", "Kibic"
OTHER_SHORT, OTHER_FULL = "O", "Inne"
REFEREE_SHORT, REFEREE_FULL = "A", "Sędzia"


PROFILE_TYPE_PLAYER = "player"
PROFILE_TYPE_COACH = "coach"
PROFILE_TYPE_CLUB = "club"
PROFILE_TYPE_GUEST = "guest"
PROFILE_TYPE_SCOUT = "scout"
PROFILE_TYPE_MANAGER = "manager"
PROFILE_TYPE_OTHER = "other"
PROFILE_TYPE_REFEREE = "referee"


PROFILE_TYPE_SHORT_MAP = {
    PROFILE_TYPE_PLAYER: PLAYER_SHORT,
    PROFILE_TYPE_COACH: COACH_SHORT,
    PROFILE_TYPE_CLUB: CLUB_SHORT,
    PROFILE_TYPE_GUEST: GUEST_SHORT,
    PROFILE_TYPE_SCOUT: SCOUT_SHORT,
    PROFILE_TYPE_MANAGER: MANAGER_SHORT,
    PROFILE_TYPE_OTHER: OTHER_SHORT,
    PROFILE_TYPE_REFEREE: REFEREE_SHORT,
}

PROFILE_TYPE_MAP = {
    PLAYER_SHORT: PROFILE_TYPE_PLAYER,
    COACH_SHORT: PROFILE_TYPE_COACH,
    CLUB_SHORT: PROFILE_TYPE_CLUB,
    MANAGER_SHORT: PROFILE_TYPE_MANAGER,
    SCOUT_SHORT: PROFILE_TYPE_SCOUT,
    GUEST_SHORT: PROFILE_TYPE_GUEST,
    REFEREE_SHORT: PROFILE_TYPE_REFEREE,
    OTHER_SHORT: PROFILE_TYPE_OTHER,
}

ACCOUNT_ROLES = (
    (PLAYER_SHORT, PLAYER_FULL),
    (COACH_SHORT, COACH_FULL),
    (CLUB_SHORT, CLUB_FULL),
    (MANAGER_SHORT, MANAGER_FULL),
    (SCOUT_SHORT, SCOUT_FULL),
    (GUEST_SHORT, GUEST_FULL),
    (OTHER_SHORT, OTHER_FULL),
    (REFEREE_SHORT, REFEREE_FULL),
)

CLUB_ROLE_PRESES = "Prezes"
CLUB_ROLE_BOARD_MEMBER = "Dyrektor sportowy"
CLUB_ROLE_SPORT_DIRECTOR = "Członek zarządu"
CLUB_ROLE_SCOUT_DIRECTOR = "Dyrektor skautingu"
CLUB_ROLE_TEAM_LEADER = "Kierownik drużyny"
CLUB_ROLE_OTHERS = "Inne"

CLUB_ROLES = (
    ("P", CLUB_ROLE_PRESES),
    ("DSp", CLUB_ROLE_BOARD_MEMBER),
    ("CZ", CLUB_ROLE_SPORT_DIRECTOR),
    ("DSk", CLUB_ROLE_SCOUT_DIRECTOR),
    ("KD", CLUB_ROLE_TEAM_LEADER),
    ("O", CLUB_ROLE_OTHERS),
)


DATA_FULFILL_STATUS = (
    (1, "Uzupełnione"),
    (2, "Częściowo uzupełnione"),
    (3, "Nie uzupełnione"),
)


class RoleShortcut(str, Enum):
    PLAYER: str = PLAYER_SHORT
    COACH: str = COACH_SHORT
    CLUB: str = CLUB_SHORT
    MANAGER: str = MANAGER_SHORT
    SCOUT: str = SCOUT_SHORT
    FAN: str = GUEST_SHORT


class ProfileDataScore(str, Enum):
    ONE = 1
    TWO = 2
    THREE = 3


# Transfer status choices
@dataclass
class TransferStatusChoices:
    LOOKING_FOR_CLUB = "Szukam klubu"
    CONSIDER_OFFERS = "Rozważę propozycje"
    NOT_LOOKING_FOR_CLUB = "Nie szukam klubu"
    FOOTBALL_PENSION = "Piłkarska emerytura"


TRANSFER_STATUS_CHOICES = (
    ("1", TransferStatusChoices.LOOKING_FOR_CLUB),
    ("2", TransferStatusChoices.CONSIDER_OFFERS),
    ("3", TransferStatusChoices.NOT_LOOKING_FOR_CLUB),
    ("4", TransferStatusChoices.FOOTBALL_PENSION),
)


@dataclass
class TransferStatusAdditionalInfo:
    """Enum for transfer request additional info field."""

    AVAILABLE_RIGHT_NOW = "Dostępny od zaraz"
    AFTER_CONTUSION = "Wracam po kontuzji"
    RENT_AVAILABLE = "Możliwe wypożyczenie"
    AFTER_RELOCATION = "Po przeprowadzce"
    PARTY_TIME_STUDY = "Studiuje zaoczne"
    IRREGULAR_WORKING_MODE = "Pracuje w nieregularnym trybie pracy"


TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES = (
    ("1", TransferStatusAdditionalInfo.AVAILABLE_RIGHT_NOW),
    ("2", TransferStatusAdditionalInfo.AFTER_CONTUSION),
    ("3", TransferStatusAdditionalInfo.RENT_AVAILABLE),
    ("4", TransferStatusAdditionalInfo.AFTER_RELOCATION),
    ("5", TransferStatusAdditionalInfo.PARTY_TIME_STUDY),
    ("6", TransferStatusAdditionalInfo.IRREGULAR_WORKING_MODE),
)


class PlayerPositions(str, Enum):
    """Enum for transfer request positions field."""

    GOALKEEPER = "Bramkarz"
    CENTER_BACK = "Środkowy Obrońca"
    LEFT_BACK = "Lewy Obrońca"
    RIGHT_BACK = "Prawy Obrońca"
    DEFENSIVE_MIDFIELDER = "Defensywny Pomocnik #6"
    CENTRAL_MIDFIELDER = "Środkowy Pomocnik #8"
    OFFENSIVE_MIDFIELDER = "Ofensywny Pomocnik #10"
    LEFT_MIDFIELDER = "Lewy Pomocnik"
    RIGHT_MIDFIELDER = "Prawy Pomocnik"
    ATTACKER = "Napastnik"
    WINGER = "Skrzydłowy"

    @classmethod
    def values(cls) -> List[str]:
        """Returns values as list of strings."""
        return [member.value for member in cls]


class PlayerPositionShortcutsEN(str, Enum):
    """Enum for transfer request positions field."""

    GOALKEEPER = "GK"
    CENTER_BACK = "CB"
    LEFT_BACK = "LB"
    RIGHT_BACK = "RB"
    DEFENSIVE_MIDFIELDER = "DM"
    CENTRAL_MIDFIELDER = "CM"
    OFFENSIVE_MIDFIELDER = "CAM"
    LEFT_MIDFIELDER = "LM"
    RIGHT_MIDFIELDER = "RM"
    ATTACKER = "F"
    WINGER = "W"

    @classmethod
    def values(cls) -> List[str]:
        """Returns values as list of strings."""
        return [member.value for member in cls]


class PlayerPositionShortcutsPL(str, Enum):
    """Enum for transfer request positions field."""

    GOALKEEPER = "BR"
    CENTER_BACK = "ŚO"
    LEFT_BACK = "LO"
    RIGHT_BACK = "PO"
    DEFENSIVE_MIDFIELDER = "DP"
    CENTRAL_MIDFIELDER = "ŚP"
    OFFENSIVE_MIDFIELDER = "OP"
    LEFT_MIDFIELDER = "LP"
    RIGHT_MIDFIELDER = "PP"
    ATTACKER = "N"
    WINGER = "SK"

    @classmethod
    def values(cls) -> List[str]:
        """Returns values as list of strings."""
        return [member.value for member in cls]


# Transfer request choices
@dataclass
class TransferRequestTrainings:
    """Enum for transfer request trainings field."""

    ONE_TWO = "1-2 treningi tygodniowo"
    THREE_FOUR = "3-4 treningi tygodniowo"
    FIVE_OR_MORE = "5+ treningów tygodniowo"


TRANSFER_TRAININGS_CHOICES = (
    ("1", TransferRequestTrainings.ONE_TWO),
    ("2", TransferRequestTrainings.THREE_FOUR),
    ("3", TransferRequestTrainings.FIVE_OR_MORE),
)


@dataclass
class TransferRequestAdditionalInfo:
    """Enum for transfer request additional info field."""

    TRANSPORT_REFUND = "Zwrot lub organizacja transportu"
    SHOES_OR_GLOVES_REFUND = "Zwrot za buty lub rękawice"
    TRAINING_EQUIPMENT = "Sprzęt treningowy"
    TRAINING_FACILITIES = "Dobre zaplecze treningowe"
    WINNING_BONUSES = "Premie za wygrane"
    PHYSIOTHERAPIST = "Fizjoterapeuta w sztabie"
    GYM = "Siłownia do dyspozycji"
    PROMOTION_FIGHT = "Walka o awans"
    EXPERIENCED_COACH = "Doświadczony trener"


TRANSFER_BENEFITS_CHOICES = (
    ("1", TransferRequestAdditionalInfo.TRANSPORT_REFUND),
    ("2", TransferRequestAdditionalInfo.SHOES_OR_GLOVES_REFUND),
    ("3", TransferRequestAdditionalInfo.TRAINING_EQUIPMENT),
    ("4", TransferRequestAdditionalInfo.TRAINING_FACILITIES),
    ("5", TransferRequestAdditionalInfo.WINNING_BONUSES),
    ("6", TransferRequestAdditionalInfo.PHYSIOTHERAPIST),
    ("7", TransferRequestAdditionalInfo.GYM),
    ("8", TransferRequestAdditionalInfo.PROMOTION_FIGHT),
    ("9", TransferRequestAdditionalInfo.EXPERIENCED_COACH),
)


@dataclass
class TransferRequestSalary:
    """Enum for transfer request salary field."""

    ONE = "0 - 499 zł"
    TWO = "500 - 999 zł"
    THREE = "1000 - 1999 zł"
    FOUR = "2000 - 3999 zł"
    FIVE = "4000+ zł"


TRANSFER_SALARY_CHOICES = (
    ("1", TransferRequestSalary.ONE),
    ("2", TransferRequestSalary.TWO),
    ("3", TransferRequestSalary.THREE),
    ("4", TransferRequestSalary.FOUR),
    ("5", TransferRequestSalary.FIVE),
)


@dataclass
class TransferRequestStatus:
    """Enum for transfer request status field."""

    UNKNOWN = "Nieznany"
    LOOKING_FOR_A_PLAYER = "Szukam piłkarzy"
    NOT_LOOKING_FOR_A_PLAYER = "Nie szukam piłkarzy"


TRANSFER_REQUEST_STATUS_CHOICES = (
    ("1", TransferRequestStatus.UNKNOWN),
    ("2", TransferRequestStatus.LOOKING_FOR_A_PLAYER),
    ("3", TransferRequestStatus.NOT_LOOKING_FOR_A_PLAYER),
)
