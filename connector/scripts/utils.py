import re
from django.core.exceptions import ObjectDoesNotExist
from mapper.models import MapperSource, MapperEntity, Mapper

#mapper sources
NEW_LNP_SOURCE, _ = MapperSource.objects.get_or_create(name="NEW_LNP")
NEW_ADDITIONAL_LNP_SOURCE, _ = MapperSource.objects.get_or_create(name="NEW_ADDITIONAL_LNP")

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


def get_mapper(target_id: str):
    try:
        entity = MapperEntity.objects.get(mapper_id=target_id)
    except ObjectDoesNotExist:
        pass
    else:
        return Mapper.objects.get(mapperentity=entity)


def create_mapper(**kwargs):
    mapper = Mapper.objects.create()
    for source, value in kwargs.items():
        MapperEntity.objects.create(
            target=mapper,
            source=MapperSource.objects.get(name=source),
            mapper_id=value["id"],
            description=value["desc"],
        )
    return mapper


def unify_name(obj_name: str, remove_roman_signs: bool = True) -> str:
    """
    Remove redundant phrases from Club/Team name
    """
    for t_from, t_to in NAMES_BLACKLISTED_PHRASES:
        obj_name = obj_name.replace(t_from, t_to)
    if remove_roman_signs:
        obj_name = re.sub(r"\b([IΙ]X|[IΙ]V|V?[IΙ]{0,3})\b\.?", "", obj_name)
    unified_name = list(
        filter(
            lambda word: len(word) > 3 and word not in TO_CUT,
            re.sub(" +", " ", re.sub("[0-9]", "", obj_name)).strip().split(),
        )
    )
    capitalized = " ".join(
        [word.capitalize() if len(word) > 3 else word for word in unified_name]
    )
    return capitalized
