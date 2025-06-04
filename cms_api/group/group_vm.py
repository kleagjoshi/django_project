from rest_framework import serializers
from cms_api.models import Group, CourseLecturer, Student
from cms_api.enums import GroupStatus


class GroupStudentSimpleVM(serializers.Serializer):
    """Simple Student ViewModel for groups"""
    id = serializers.IntegerField()
    user_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()


class CourseLecturerGroupVM(serializers.Serializer):
    """Course Lecturer ViewModel for groups"""
    id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    lecturer_id = serializers.IntegerField()
    lecturer_name = serializers.CharField()


class GroupCreateVM(serializers.Serializer):
    """Group Creation ViewModel"""
    classroom = serializers.CharField(max_length=100)
    start_date = serializers.DateTimeField()
    duration = serializers.IntegerField(min_value=1, help_text="Duration in days")
    course_lecturer_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

    def validate_course_lecturer_id(self, value):
        """Validate that the course lecturer exists"""
        if not CourseLecturer.objects.filter(id=value).exists():
            raise serializers.ValidationError("CourseLecturer does not exist")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Validate student IDs
        for student_id in data.get('student_ids', []):
            if not Student.objects.filter(id=student_id).exists():
                raise serializers.ValidationError(f"Student with ID {student_id} does not exist")

        return data


class GroupEditVM(serializers.Serializer):
    """Group Edit ViewModel"""
    classroom = serializers.CharField(max_length=100)


class GroupGetVM(serializers.Serializer):
    """Full Group ViewModel with relationships"""
    id = serializers.IntegerField()
    classroom = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField(read_only=True)
    duration = serializers.IntegerField(read_only=True, help_text="Duration in days")
    status = serializers.ChoiceField(choices=GroupStatus.choices)
    course_lecturer_id = serializers.IntegerField()
    course_lecturer = CourseLecturerGroupVM()
    students = GroupStudentSimpleVM(many=True)


class GroupSimpleVM(serializers.Serializer):
    """Simple Group ViewModel"""
    id = serializers.IntegerField()
    classroom = serializers.CharField()
    course_name = serializers.CharField()
    lecturer_name = serializers.CharField()
    status = serializers.ChoiceField(choices=GroupStatus.choices)