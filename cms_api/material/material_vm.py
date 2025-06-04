from rest_framework import serializers
from cms_api.models import Material, Group


class MaterialVM(serializers.Serializer):
    """Material Creation/Update ViewModel"""
    topic = serializers.CharField(max_length=200)
    description = serializers.CharField()
    week = serializers.IntegerField(min_value=1)
    link = serializers.URLField()

    def validate_link(self, value):
        """Validate that the link is a valid URL"""
        if not value:
            raise serializers.ValidationError("Link is required")
        return value


class MaterialGetVM(serializers.Serializer):
    """Material Retrieval ViewModel"""
    id = serializers.IntegerField()
    topic = serializers.CharField()
    description = serializers.CharField()
    week = serializers.IntegerField()
    link = serializers.URLField()


class MaterialCreateVM(serializers.Serializer):
    """Material Creation ViewModel with Group validation"""
    topic = serializers.CharField(max_length=200)
    description = serializers.CharField()
    week = serializers.IntegerField(min_value=1)
    link = serializers.URLField()
    group_id = serializers.IntegerField()

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate_link(self, value):
        """Validate that the link is a valid URL"""
        if not value:
            raise serializers.ValidationError("Link is required")
        return value


class MaterialUpdateVM(serializers.Serializer):
    """Material Update ViewModel"""
    topic = serializers.CharField(max_length=200)
    description = serializers.CharField()
    week = serializers.IntegerField(min_value=1)
    link = serializers.URLField()

    def validate_link(self, value):
        """Validate that the link is a valid URL"""
        if not value:
            raise serializers.ValidationError("Link is required")
        return value