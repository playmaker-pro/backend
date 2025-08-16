from rest_framework import serializers

from labels import models
from api.i18n import I18nSerializerMixin
from labels.translations import translate_label_description, translate_catalog_name


class LabelDefinitionSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    label_description = serializers.SerializerMethodField()
    catalog_name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.LabelDefinition
        fields = "__all__"
        
    def get_label_description(self, obj) -> str:
        """
        Return translated label description.
        """
        # Ensure language is activated for translation
        self._activate_context_language()
        if obj.label_description:
            return translate_label_description(obj.label_description)
        return ""
        
    def get_catalog_name(self, obj) -> str:
        """
        Return translated catalog name.
        """
        # Ensure language is activated for translation  
        self._activate_context_language()
        if obj.catalog_name:
            return translate_catalog_name(obj.catalog_name)
        return ""
