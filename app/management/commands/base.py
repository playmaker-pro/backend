import hashlib
from dataclasses import dataclass
from functools import lru_cache
import enum
from typing import List


class TypeEnum(enum.Enum):
    WRITE = "W"
    READ = "R"
    MODERATE = "M"


class Field:
    def __init__(self, name: str, value: str = None):
        self.name, self.type = self.decode_name_with_type(name)
        self.value = value

    def __str__(self):
        return f"[{self.type}] {self.name} ({self.value})"

    def __repr__(self):
        return self.__str__()

    @lru_cache()
    def decode_name_with_type(self, name: str) -> tuple:
        _name = name.split('] ')[1]
        if f"[{TypeEnum.WRITE.value}]" in name:
            _type = TypeEnum.WRITE.value
        if f"[{TypeEnum.READ.value}]" in name:
            _type = TypeEnum.READ.value
        if f"[{TypeEnum.MODERATE.value}]" in name:
            _type = TypeEnum.READ.value
        return _name, _type


class Structure(dict):
    def get_write_read_field_names(self) -> List[Field]:
        w_output = []
        r_output = []
        for name, value in self.items():
            f = Field(name, value)
            if f.type == TypeEnum.WRITE.value:
                w_output.append(f.name)
            if f.type == TypeEnum.READ.value:
                r_output.append(f.name)
        common_field_names = list(set(w_output) & set(r_output))
        output = []
        for name, value in self.items():
            f = Field(name, value)
            if f.name in common_field_names and f.type == TypeEnum.READ.value:
                output.append(f)      
        return output

    def get_write_field_names(self):
        output = []
        for name, value in self.items():
            if "[W]" in name:
                output.append(name)
        return output

    def get_write_field_names(self):
        output = []
        for name, value in self.items():
            if "[R]" in name:
                output.append(name)
        return output


class BaseCsvDump:
    _checksum_field_name = "checksum"

    def _moderate_field(self, name: str) -> str:
        return f'[M] {name}'

    def _read_field(self, name: str) -> str:
        return f'[R] {name}'

    def _write_field(self, name: str) -> str:
        return f"[W] {name}"

    def _get_checksum_field(self) -> str:
        return self._moderate_field(self._checksum_field_name)

    def calculate_checksum(self, structure: Structure) -> str:
        fields = structure.get_write_read_field_names()
        values = [str(field.value) for field in fields]
        str_values = ' '.join(values).encode('utf-8')
        return hashlib.md5(str_values).hexdigest()

    # def get_base_object_structure(self, instace):
    #     return Structure({
            
    #     })
    def get_player_structure(self, instance):
        return Structure({
            self._read_field("id"): instance.user.id,
            self._read_field("full_name"): instance.user.get_full_name(),
            self._read_field("team_object"): instance.team_object.id if instance.team_object else None,
            self._read_field("display_team"): instance.display_team,
            self._read_field("display_league"): instance.display_league,
            self._read_field("phone"): instance.phone,
            self._write_field("team_object"): None,
        })

    def get_team_structure(self, instance):
        return Structure({
            self._read_field("id"): instance.id,
            self._read_field("name"): instance.name,
            self._read_field("mapping"): instance.mapping,
            self._read_field("seniorty"): instance.display_seniority,
            self._read_field("display_league"): instance.display_league,
            self._read_field("league_object"): instance.league.id if instance.league else None,
            self._read_field("data_mapper_id"): instance.data_mapper_id,
            self._read_field("display_club"): instance.display_club,
            self._read_field("club_object"): instance.club.id if instance.club else None,
            # read fields
            self._write_field("name"): None,
            self._write_field("league_object"): None,
            self._write_field("data_mapper_id"): None,
            self._write_field("mapping"): None,
            self._write_field("club_object"): None,
        })


class BaseCommandCsvHandler:
    name_template = '1_{}_dump_v1.csv'

    def get_csv_name(self, marker: str):
        return self.name_template.format(marker)

    def add_arguments(self, parser):
        """
        :type: player|team
        :marker:
            defines the core name of dump to be recognized later on
        """
        parser.add_argument("type", type=str)
        parser.add_argument("-m", "--marker", type=str, default=None)
        parser.add_argument("-d", "--dryrun", type=bool, default=False)

