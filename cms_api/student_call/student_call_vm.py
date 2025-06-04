from rest_framework import serializers
from cms_api.models import Student, Call, StudentCall
from ..student.student_vm import StudentVM


class StudentCallCreateVM(serializers.Serializer):
    """Student Call Creation ViewModel"""
    student_id = serializers.IntegerField()
    call_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_call_id(self, value):
        """Validate that the call exists"""
        if not Call.objects.filter(id=value).exists():
            raise serializers.ValidationError("Call does not exist")
        return value

    def validate(self, data):
        """Validate that the student call relationship doesn't already exist"""
        student_id = data.get('student_id')
        call_id = data.get('call_id')

        if student_id and call_id:
            if StudentCall.objects.filter(student_id=student_id, call_id=call_id).exists():
                raise serializers.ValidationError("Student is already assigned to this call")

        return data


class StudentCallDeleteVM(serializers.Serializer):
    """Student Call Deletion ViewModel"""
    student_id = serializers.IntegerField()
    call_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_call_id(self, value):
        """Validate that the call exists"""
        if not Call.objects.filter(id=value).exists():
            raise serializers.ValidationError("Call does not exist")
        return value

    def validate(self, data):
        """Validate that the student call relationship exists"""
        student_id = data.get('student_id')
        call_id = data.get('call_id')

        if student_id and call_id:
            if not StudentCall.objects.filter(student_id=student_id, call_id=call_id).exists():
                raise serializers.ValidationError("Student call relationship does not exist")

        return data


class StudentCallVM(serializers.Serializer):
    """Student Call ViewModel"""
    id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    call_id = serializers.IntegerField()
    student_name = serializers.CharField(required=False)
    student_surname = serializers.CharField(required=False)
    call_capacity = serializers.IntegerField(required=False)
    call_date_added = serializers.DateTimeField(required=False)


class CallStudentsRequestVM(serializers.Serializer):
    """Request ViewModel for getting students by call ID"""
    call_id = serializers.IntegerField()

    def validate_call_id(self, value):
        """Validate that the call exists"""
        if not Call.objects.filter(id=value).exists():
            raise serializers.ValidationError("Call does not exist")
        return value


class StudentCallsListVM(serializers.Serializer):
    """Student Calls List ViewModel"""
    student_calls = StudentCallVM(many=True)
    total_count = serializers.IntegerField()


class StudentCallBulkCreateVM(serializers.Serializer):
    """Bulk Student Call Creation ViewModel"""
    call_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100  # Reasonable limit
    )

    def validate_call_id(self, value):
        """Validate that the call exists"""
        if not Call.objects.filter(id=value).exists():
            raise serializers.ValidationError("Call does not exist")
        return value

    def validate_student_ids(self, value):
        """Validate that all students exist"""
        existing_students = Student.objects.filter(id__in=value).values_list('id', flat=True)
        missing_students = set(value) - set(existing_students)

        if missing_students:
            raise serializers.ValidationError(f"Students with IDs {list(missing_students)} do not exist")

        return value

    def validate(self, data):
        """Validate that no duplicate relationships would be created"""
        call_id = data.get('call_id')
        student_ids = data.get('student_ids', [])

        if call_id and student_ids:
            existing_relationships = StudentCall.objects.filter(
                call_id=call_id,
                student_id__in=student_ids
            ).values_list('student_id', flat=True)

            if existing_relationships:
                raise serializers.ValidationError(
                    f"Students with IDs {list(existing_relationships)} are already assigned to this call"
                )

        return data


class StudentCallBulkDeleteVM(serializers.Serializer):
    """Bulk Student Call Deletion ViewModel"""
    call_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )

    def validate_call_id(self, value):
        """Validate that the call exists"""
        if not Call.objects.filter(id=value).exists():
            raise serializers.ValidationError("Call does not exist")
        return value

    def validate_student_ids(self, value):
        """Validate that all students exist"""
        existing_students = Student.objects.filter(id__in=value).values_list('id', flat=True)
        missing_students = set(value) - set(existing_students)

        if missing_students:
            raise serializers.ValidationError(f"Students with IDs {list(missing_students)} do not exist")

        return value