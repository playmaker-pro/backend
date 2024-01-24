from typing import List


def convert_bool(key: str, value: str) -> bool:
    """convert GET param as bool, raise exception if value isn't bool"""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    raise ValueError(f"Parameter {key} require bool value <true/false>, got: '{value}'")


def convert_int(key: str, value: str) -> int:
    """convert GET param as integer, raise exception if value isn't int"""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Parameter {key} require integer value, got: '{value}'")


def convert_str(key: str, value: str) -> str:
    """convert GET param as string"""
    return value  # no need to validate I guess


def convert_float(key: str, value: str) -> float:
    """convert GET param as float"""
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Parameter {key} require float value, got: '{value}'")


def convert_int_list(key: str, value: list) -> list:
    """convert GET param as array of integers"""
    return [convert_int(key, sub_val) for sub_val in value]


def convert_str_list(key: str, value: list) -> list:
    """convert GET param as array of strings"""
    return [convert_str(key, sub_val) for sub_val in value]


def convert_list_with_string_to_int(_, value: List[str]) -> List[int]:
    """convert GET param as array of strings to array of integers"""
    return [int(val) for val in value if val.isdigit()]


LIST_PARSERS = [convert_int_list, convert_str_list, convert_list_with_string_to_int]
