from rest_framework import serializers
from cms_api.models import Call, Course


class CallCreateVM(serializers.Serializer):
    """Call Creation ViewModel"""
    capacity = serializers.IntegerField(min_value=1)
    course_id = serializers.IntegerField()
    application_deadline = serializers.DateTimeField()

    def validate_course_id(self, value):
        """Validate that the course exists"""
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Course does not exist")
        return value


class CallVM(serializers.Serializer):
    """Full Call ViewModel with course details"""
    id = serializers.IntegerField()
    capacity = serializers.IntegerField()
    date_added = serializers.DateTimeField()
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    course_duration = serializers.IntegerField()
    course_level = serializers.CharField()
    course_price = serializers.IntegerField()


class CallEditVM(serializers.Serializer):
    """Call Edit ViewModel"""
    capacity = serializers.IntegerField(min_value=1)


class CallSimpleVM(serializers.Serializer):
    """Simple Call ViewModel"""
    id = serializers.IntegerField()
    capacity = serializers.IntegerField()
    course_name = serializers.CharField()