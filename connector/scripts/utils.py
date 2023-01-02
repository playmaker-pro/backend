import re
from django.core.exceptions import ObjectDoesNotExist
from mapper.models import MapperSource, MapperEntity, Mapper
from mapper.enums import RE_ROMAN

LNP_SOURCE, _ = MapperSource.objects.get_or_create(name="LNP")

NAMES_BLACKLISTED_PHRASES = (
    ("/", " "),
    ('"', ""),
    ("SP. Z O.O.", ""),
    ("S.A.", ""),
    ("SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", ""),
    ("SPÓŁKA Z O. O.", ""),
    ("SP. Z.O.O", ""),
    (".", ""),
)

TO_CUT = [
        "KSAP",
        "GLKS",
        "CWKS",
        "MLKS",
        "MUKS",
        "APIS",
        "MOSP",
        "KTS-K",
        "CWZS",
        "ULKS",
        "GMKS",
        "WRKS",
        "MGKS",
        "BPAP",
        "MŁKS",
        "BBTS",
        "SSIR",
        "GSKS",
        "LMKS",
        "ZZPD",
        "LPFA",
        "ELPA",
        "GZPN",
        "(RW)",
        "(RJ)",
    ]

MAPPER_ENTITY_SOURCE, _ = MapperSource.objects.get_or_create(name="LNP")


def get_mapper(target_id: str):
    try:
        entity = MapperEntity.objects.get(mapper_id=target_id)
    except ObjectDoesNotExist:
        pass
    else:
        return entity.target


def create_mapper(*args):
    mapper = Mapper.objects.create()
    for entity in args:
        MapperEntity.objects.create(
            target=mapper,
            source=MAPPER_ENTITY_SOURCE,
            mapper_id=entity["id"],
            description=entity["desc"],
            related_type=entity["related_type"],
            database_source=entity["database_source"],
        )
    return mapper


def unify_club_name(obj_name: str) -> str:
    """
    Remove redundant phrases from Club name
    """

    for t_from, t_to in NAMES_BLACKLISTED_PHRASES:
        obj_name = obj_name.replace(t_from, t_to)
    obj_name = re.sub(r"\b([IΙ]X|[IΙ]V|V?[IΙ]{0,3})\b\.?", "", obj_name)
    unified_name = list(
        filter(
            lambda word: word not in TO_CUT,
            re.sub(" +", " ", re.sub("[0-9]", "", obj_name)).strip().split(),
        )
    )
    capitalized = " ".join(
        [word.capitalize() if len(word) > 3 else word for word in unified_name]
    )
    return capitalized


def unify_team_name(obj_name: str) -> str:
    """
    Remove redundant phrases from Team name
    """
    for t_from, t_to in NAMES_BLACKLISTED_PHRASES:
        obj_name = obj_name.replace(t_from, t_to)
    unified_name = list(
        filter(
            lambda word: word not in TO_CUT or re.match(RE_ROMAN, word).group(),
            re.sub(" +", " ", re.sub("[0-9]", "", obj_name)).strip().split(),
        )
    )
    if unified_name:
        if re.match(RE_ROMAN, unified_name[0]).group():
            unified_name[0], unified_name[-1] = unified_name[-1], unified_name[0]
    capitalized = " ".join(
        [word.capitalize() if len(word) > 3 else word for word in unified_name]
    )
    return capitalized
