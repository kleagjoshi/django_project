from rest_framework import serializers
from cms_api.models import Student, ApplicationUser, GroupStudent
from cms_api.enums import GenderChoices, StudentGroupStatus


class StudentCreateVM(serializers.Serializer):
    """Student Creation ViewModel"""
    user_id = serializers.CharField(max_length=255)
    employed = serializers.BooleanField(default=False)

    def validate_user_id(self, value):
        """Validate that the user exists and is not already a student"""
        if not ApplicationUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist")

        # Check if user is already a student
        if Student.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("User is already a student")

        return value


class StudentEditVM(serializers.Serializer):
    """Student Edit ViewModel"""
    person_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    father_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    birthday = serializers.DateField(required=False, allow_null=True)
    birth_place = serializers.CharField(max_length=200, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=GenderChoices.choices, required=False, allow_blank=True)
    employed = serializers.BooleanField()

    def validate_name(self, value):
        """Validate name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

    def validate_surname(self, value):
        """Validate surname is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Surname cannot be empty")
        return value.strip()


class StudentVM(serializers.Serializer):
    """Student Retrieval ViewModel"""
    id = serializers.IntegerField()
    person_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()
    father_name = serializers.CharField()
    birthday = serializers.DateField()
    birth_place = serializers.CharField()
    gender = serializers.CharField()
    employed = serializers.BooleanField()
    user_id = serializers.CharField()
    is_enabled = serializers.BooleanField(required=False)


class StudentWithGroupVM(serializers.Serializer):
    """Student ViewModel with Group Context - includes group_student_id"""
    id = serializers.IntegerField()
    person_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()
    father_name = serializers.CharField()
    birthday = serializers.DateField()
    birth_place = serializers.CharField()
    gender = serializers.CharField()
    employed = serializers.BooleanField()
    user_id = serializers.CharField()
    group_student_id = serializers.IntegerField()  # The GroupStudent relationship ID


class StudentSimpleVM(serializers.Serializer):
    """Simple Student ViewModel for dropdowns"""
    id = serializers.IntegerField()
    user_id = serializers.CharField()
    name = serializers.CharField()
    surname = serializers.CharField()


class StudentSearchVM(serializers.Serializer):
    """Student Search ViewModel"""
    name = serializers.CharField(required=False, allow_blank=True)
    surname = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate that at least one search parameter is provided"""
        name = data.get('name', '').strip()
        surname = data.get('surname', '').strip()

        if not name and not surname:
            raise serializers.ValidationError("At least one of name or surname must be provided")

        return {
            'name': name,
            'surname': surname
        }


class StudentStatusUpdateVM(serializers.Serializer):
    """Student Status Update ViewModel"""
    student_id = serializers.IntegerField()
    new_status = serializers.ChoiceField(choices=StudentGroupStatus.choices)

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate(self, data):
        """Validate that the student has a group assignment"""
        student_id = data.get('student_id')
        if student_id and not GroupStudent.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError("Student is not assigned to any group")
        return data


class StudentReturnVM(serializers.Serializer):
    """Student Return ViewModel"""
    student_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value