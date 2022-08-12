# -*- coding: utf-8 -*-
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class BaseModelImport:    
    
    def __init__(self, data_frame, model, *args, **kwargs):
        self.data_frame = self.remove_NaN(data_frame)        
        self.model = model
        self.obj = {}
        self.import_data()
        
    def remove_NaN(self, df):
        return df.fillna('')
        
    def import_data(self): #override in child
        pass
        
        
class CrmXmlImport(BaseModelImport):
    
    CRM_ADMINS = {
        "Adrian Mazurek": "adrianmazurek8@gmail.com",
        "Rafał Stryczek": "stryku2@gmail.com",
        "Piotr Stawarczyk": "stawaRRR@gmail.com",
        "Michał Szoja": "szojos8@gmail.com",
        "Łukasz Cygan": "cygi9318@gmail.com",
        "Jarosław Sobstyl": "jaroslaw.sobstyl@gmail.com",
        "Jan Małysz": "janek.malysz@gmail.com",
        "Rafał Zieliński": "zielaj1910@gmail.com",
        "Hubert Kujawa": "hubert.w.kujawa@gmail.com",
        "Filip Słowakiewicz": "filipslowakiewicz1@gmail.com",
        "Szymon Kobylnik": "szymon@playmaker.pro",
        "Dennis Gordzielik": "dennis@playmaker.pro",
        "Mateusz Musiał": "mateusz@playmaker.pro",
        "Jacek Jasiński": "jacek@playmaker.pro",
    }
    
    POSSIBLE_UNIQUE_FIELDS = (
        ("phone", "tel"),
        ("email", "@"),
        ("twitter_url", "TT"),
        ("facebook_url", "FB"),
        ("instagram_url", "IG"),
        ("website_url", "www"),
    )
    
    def check_contact(self, info):
        if not any(val in [
            "phone",
            "email",
            "twitter_url",
            "facebook_url",
            "instagram_url",
            "website_url"] for val in self.obj.keys()):
            self.fetch_from_string(info)
        
    def fetch_from_string(self, val):
        try:
            fields = {k.strip():v.strip() for k, v in [v.split(": ") for v in val.split("|") if val]}
        except ValueError: return
        for field, key in self.POSSIBLE_UNIQUE_FIELDS:
            if field not in self.obj.keys() and key in fields.keys():
                self.obj[field] = fields[key]
    
    def created_by(self, val):
        if val:
            first_name, last_name = self.split_full_name(val)
            attrs = {
                "first_name": first_name,
                "last_name": last_name,
                "email": self.CRM_ADMINS[val]
                }
            user = self.get_or_create_user_for_management(attrs)            
            self.obj['created_by'] = user
            
    def create_object(self, *args, **kwargs):
        obj = None
        if kwargs.get("info"):
            self.check_contact(kwargs["info"])
        obj = self.get_object_or_none(self.model, **self.obj)
        if not obj and self.obj:
            self.model.objects.create(**self.obj) if self.obj else None
            print("Created: ", self.model, self.obj)
        self.obj.clear()
    
    def date_created(self, val):
        try:
            self.obj["date_created"] = timezone.make_aware(val)
        except ValueError:
            pass
    
    def split_full_name(self, full_name):
        split = full_name.split(" ") 
        try:
            return split[0], split[1]
        except (KeyError, IndexError):
            return full_name, ""       

    def get_object_or_none(self, model=User, *args, **kwargs):
        obj = None
        try:
            del kwargs["date_created"]
        except KeyError: pass
        try:
            obj = model.objects.get(**kwargs)
        except (ObjectDoesNotExist, MultipleObjectsReturned): pass
        
        return obj
        
    def create_crm_group(self):
        content_type = ContentType.objects.filter(app_label='crm')
        permissions = [
            Permission.objects
                .filter(content_type=ct) for ct in [ct for ct in content_type]]
        permissions_raw = []
        for permission_array in permissions:
            permissions_raw += permission_array
        self.group, _ = Group.objects.get_or_create(name="CRM Admin")
        for permission in permissions_raw:
            self.group.permissions.add(permission)
        
           
    def get_or_create_user_for_management(self, attrs):
        try:
            user = User.objects.get(**attrs)
        except ObjectDoesNotExist:
            user = User.objects.create(**attrs)
        user.groups.add(self.group)
        return user
    
