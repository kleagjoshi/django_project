from rest_framework import serializers
from cms_api.models import Lecturer, Course, ApplicationUser
from cms_api.enums import GenderChoices


class CourseOfLecturerVM(serializers.Serializer):
    """Course ViewModel for lecturers"""
    id = serializers.IntegerField()
    course_name = serializers.CharField()
    course_id = serializers.IntegerField()


class LecturerCreateVM(serializers.Serializer):
    """Lecturer Creation ViewModel"""
    contract_start = serializers.DateField()
    contract_end = serializers.DateField()
    university_degree = serializers.CharField(max_length=200)
    user_id = serializers.CharField()
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

    def validate_user_id(self, value):
        """Validate that the user exists"""
        if not ApplicationUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist")
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data['contract_start'] >= data['contract_end']:
            raise serializers.ValidationError("Contract end date must be after start date")

        # Validate course IDs
        for course_id in data.get('course_ids', []):
            if not Course.objects.filter(id=course_id).exists():
                raise serializers.ValidationError(f"Course with ID {course_id} does not exist")

        return data


class LecturerEditVM(serializers.Serializer):
    """Lecturer Edit ViewModel"""
    person_id = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    father_name = serializers.CharField(max_length=100)
    birthday = serializers.DateField()
    birth_place = serializers.CharField(max_length=100)
    gender = serializers.ChoiceField(choices=GenderChoices.choices)
    contract_start = serializers.DateField()
    contract_end = serializers.DateField()
    university_degree = serializers.CharField(max_length=200)
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

    def validate(self, data):
        """Cross-field validation"""
        if data['contract_start'] >= data['contract_end']:
            raise serializers.ValidationError("Contract end date must be after start date")

        # Validate course IDs
        for course_id in data.get('course_ids', []):
            if not Course.objects.filter(id=course_id).exists():
                raise serializers.ValidationError(f"Course with ID {course_id} does not exist")

        return data


class LecturerVM(serializers.Serializer):
    """Full Lecturer ViewModel with user and course details"""
    id = serializers.IntegerField()
    person_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()
    father_name = serializers.CharField()
    birthday = serializers.DateField()
    birth_place = serializers.CharField()
    gender = serializers.ChoiceField(choices=GenderChoices.choices)
    contract_start = serializers.DateField()
    contract_end = serializers.DateField()
    university_degree = serializers.CharField()
    user_id = serializers.CharField()
    courses = CourseOfLecturerVM(many=True)


class LecturerSimpleVM(serializers.Serializer):
    """Simple Lecturer ViewModel for forms"""
    id = serializers.IntegerField()
    user_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()


class LecturerSearchVM(serializers.Serializer):
    """Lecturer Search ViewModel"""
    name = serializers.CharField(required=False, allow_blank=True)
    surname = serializers.CharField(required=False, allow_blank=True)