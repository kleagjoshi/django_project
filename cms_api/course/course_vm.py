from rest_framework import serializers
from cms_api.models import Course, CourseLecturer, Call, Lecturer


class CallBaseVM(serializers.Serializer):
    """Basic Call ViewModel"""
    id = serializers.IntegerField()
    capacity = serializers.IntegerField()


class CourseLecturerVM(serializers.Serializer):
    """Course Lecturer ViewModel"""
    id = serializers.IntegerField()
    lecturer_id = serializers.IntegerField()
    lecturer_name = serializers.CharField()


class CourseVM(serializers.Serializer):
    """Full Course ViewModel with relationships"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    duration = serializers.IntegerField()
    price = serializers.IntegerField()
    level = serializers.CharField()
    calls = CallBaseVM(many=True)
    lectures = CourseLecturerVM(many=True)


class CourseSimpleVM(serializers.Serializer):
    """Simple Course ViewModel"""
    id = serializers.IntegerField()
    name = serializers.CharField()


class CourseCreateVM(serializers.Serializer):
    """Course Creation ViewModel"""
    name = serializers.CharField(max_length=200)
    duration = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=0)
    level = serializers.CharField(max_length=50)
    lecturer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class CourseEditVM(serializers.Serializer):
    """Course Edit ViewModel"""
    name = serializers.CharField(max_length=200)
    duration = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=0)
    level = serializers.CharField(max_length=50)
    lecturer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )