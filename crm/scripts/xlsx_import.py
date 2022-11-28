from utils.scripts.data_import import CrmXmlImport
from crm.models import *
import pandas as pd


class ConversationImport(CrmXmlImport):

    FIELD_MAPPING = (
        ("_date_created", "Data rozmowy"),
        ("_created_by", "Rozmowę prowadził"),
        ("_lead", "Osoba kontaktowa"),
        ("_note", "Notatka z rozmowy"),
    )

    def __init__(self, *args, **kwargs):
        kwargs["model"] = Conversation
        self.create_crm_group()
        super().__init__(*args, **kwargs)

    def _date_created(self, val):
        super().date_created(val)

    def _note(self, val):
        if val:
            self.obj["note"] = val

    def _created_by(self, val):
        super().created_by(val)

    def _lead(self, val):
        try:
            fields = {
                k.strip(): v.strip()
                for k, v in [v.split(": ") for v in val.split("|") if val]
            }
        except ValueError:
            return
        lead = None
        for field, key in self.POSSIBLE_UNIQUE_FIELDS:
            try:
                lead = self.get_object_or_none(LeadStatus, **{field: fields[key]})
            except KeyError:
                continue
            if lead:
                break
        else:
            if not lead:
                keys = list(fields.keys())
                try:
                    first_name, last_name = self.split_full_name(fields[keys[1]])
                    lead = self.get_object_or_none(
                        LeadStatus, **{"first_name": first_name, "last_name": last_name}
                    )
                except IndexError:
                    pass
        if lead:
            self.obj["lead"] = lead

    def import_data(self):
        print("Importing Conversation table...")
        for index, row in self.data_frame.iterrows():
            for db_field, xlsx_field in self.FIELD_MAPPING:
                getattr(self, db_field)(row[xlsx_field])
            if self.obj.get("lead"):
                self.create_object()


class LeadStatusImport(CrmXmlImport):

    FIELD_MAPPING = (
        ("_date_created", "Data dodania"),
        ("_created_by", "Dodał"),
        ("_team", "Klub"),
        ("_user_role", "Rola w klubie"),
        ("_full_name", "Imię nazwisko"),
        ("phone", "tel"),
        ("email", "@"),
        ("twitter_url", "TT"),
        ("facebook_url", "FB"),
        ("instagram_url", "IG"),
        ("_status", "Status na platformie"),
    )

    def __init__(self, *args, **kwargs):
        kwargs["model"] = LeadStatus
        self.teams = self.remove_NaN(kwargs["team_df"])
        self.create_crm_group()
        super().__init__(*args, **kwargs)

    def _date_created(self, val):
        super().date_created(val)

    def _user_role(self, val):
        role = self.get_object_or_none(model=Role, name=val)
        if role:
            self.obj["user_role"] = role

    def _created_by(self, val):
        super().created_by(val)

    def _team(self, val):
        if val:
            try:
                team_id = int(
                    self.teams.loc[self.teams["Rozgrywki: klub"] == val]["Team_id"]
                )
            except (ValueError, TypeError):
                return
            if team_id:
                fieldset = {"data_mapper_id": team_id}
                team = self.get_object_or_none(model=Team, **fieldset)
                if team:
                    self.obj["team"] = team

    def _status(self, val):
        try:
            fieldset = {
                "first_name": self.obj["first_name"],
                "last_name": self.obj["last_name"],
            }
        except KeyError:
            return
        else:
            if val == "Zarejestrowany":
                user = self.get_object_or_none(**fieldset)
                if user:
                    self.obj["user"] = user

    def _full_name(self, val):
        if val:
            first_name, last_name = self.split_full_name(val)
            self.obj["first_name"] = first_name
            self.obj["last_name"] = last_name

    def import_data(self):
        print("Importing LeadStatus table...")
        for _, row in self.data_frame.iterrows():
            for db_field, xlsx_field in self.FIELD_MAPPING:
                if db_field[0] == "_":
                    try:
                        getattr(self, db_field)(row[xlsx_field])
                    except KeyError:
                        continue
                elif row[xlsx_field] != "":
                    self.obj[db_field] = row[xlsx_field]
            try:
                info_row = row["Info"]
            except KeyError:
                info_row = row["Dane"]
            if not (
                len(self.obj)
                and list(self.obj.keys()) == ["date_created", "created_by"]
            ):
                self.create_object(info=info_row)


class ContactPurposeImport(CrmXmlImport):

    FIELD_MAPPING = (("name", "Rodzaj"),)

    def __init__(self, *args, **kwargs):
        kwargs["model"] = ContactPurpose
        super().__init__(*args, **kwargs)

    def import_data(self):
        print("Importing ContactPurpose table...")
        for index, row in self.data_frame.iterrows():
            for db_field, xlsx_field in self.FIELD_MAPPING:
                self.obj[db_field] = row[xlsx_field]
                self.create_object()


class RoleImport(CrmXmlImport):

    FIELD_MAPPING = (("name", "Role w klubie"),)

    def __init__(self, *args, **kwargs):
        kwargs["model"] = Role
        super().__init__(*args, **kwargs)

    def import_data(self):
        print("Importing Role table...")
        for index, row in self.data_frame.iterrows():
            for db_field, xlsx_field in self.FIELD_MAPPING:
                if row[xlsx_field] != 'Jeśli nie ma dopisz w "Role w klubie"':
                    self.obj[db_field] = row[xlsx_field]
                    self.create_object()


class ImportFromXlsx(pd.ExcelFile):

    SHEETS_MAPPING = (
        (None, "Baza klubów"),
        (RoleImport, "sett Role w klubie"),
        (ContactPurposeImport, "sett Rodzaje rozmów"),
        (LeadStatusImport, " KONTAKTY"),
        (ConversationImport, " ROZMOWY"),
    )

    def parse_dataframe(self, sheet_name):
        return pd.read_excel(self, sheet_name, header=0)

    def clear_whitespaces(self, sheet_name):
        return sheet_name.strip()

    def bulk_xlsx_import(self):
        for cls, sheet in self.SHEETS_MAPPING:
            if sheet not in self.sheet_names:
                continue
            else:
                df = self.parse_dataframe(sheet)
                if cls is None:
                    self.teams = df
                elif cls == LeadStatusImport:
                    cls(df, team_df=self.teams)
                else:
                    cls(df)
