from .functions import *

GENDER_BASED_ROLES = {
    "P": ("Piłkarz", "Piłkarka"),
    "T": ("Trener", "Trenerka"),
    "C": ("Działacz klubowy", "Działaczka klubowa"),
    "G": ("Kibic", "Kibic"),
    "M": ("Manager", "Manager"),
    "R": ("Sędzia", "Sędzia"),
    "S": ("Skaut", "Skaut"),
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
