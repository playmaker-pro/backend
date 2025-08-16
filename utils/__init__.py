from .functions import *
from django.utils.translation import gettext as _

GENDER_BASED_ROLES = {
    "P": (_("Piłkarz"), _("Piłkarka")),
    "T": (_("Trener"), _("Trenerka")),
    "C": (_("Działacz klubowy"), _("Działaczka klubowa")),
    "G": (_("Kibic"), _("Kibic")),
    "M": (_("Manager"), _("Manager")),
    "R": (_("Sędzia"), _("Sędzia")),
    "S": (_("Skaut"), _("Skaut")),
    None: ("", ""),
}
OBJECTIVE_GENDER_BASED_ROLES = {
    "P": ("piłkarza", "piłkarkę"),
    "T": ("trenera", "trenerkę"),
    "C": ("działacza klubowego", "działaczkę klubową"),
    "G": ("kibica", "kibica"),
    "M": ("managera", "managera"),
    "R": ("sędziego", "sędziego"),
    "S": ("skauta", "skauta"),
    None: ("", ""),
}
