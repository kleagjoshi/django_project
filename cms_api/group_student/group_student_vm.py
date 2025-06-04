from rest_framework import serializers
from cms_api.models import Student, Group, GroupStudent
from ..student.student_vm import StudentVM
from cms_api.enums import StudentGroupStatus


class GroupStudentCreateVM(serializers.Serializer):
    """Group Student Creation ViewModel"""
    student_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate(self, data):
        """Validate that the group student relationship doesn't already exist"""
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        
        if student_id and group_id:
            if GroupStudent.objects.filter(student_id=student_id, group_id=group_id).exists():
                raise serializers.ValidationError("Student is already assigned to this group")
        
        return data


class GroupStudentRemoveVM(serializers.Serializer):
    """Group Student Removal ViewModel"""
    student_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate(self, data):
        """Validate that the group student relationship exists"""
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        
        if student_id and group_id:
            if not GroupStudent.objects.filter(student_id=student_id, group_id=group_id).exists():
                raise serializers.ValidationError("Student is not assigned to this group")
        
        return data


class GroupStudentFeedbackVM(serializers.Serializer):
    """Group Student Feedback Update ViewModel"""
    student_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    feedback = serializers.IntegerField(min_value=0, max_value=10)

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate(self, data):
        """Validate that the group student relationship exists"""
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        
        if student_id and group_id:
            if not GroupStudent.objects.filter(student_id=student_id, group_id=group_id).exists():
                raise serializers.ValidationError("Student is not assigned to this group")
        
        return data


class GroupStudentVM(serializers.Serializer):
    """Group Student ViewModel"""
    id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    status = serializers.CharField()
    feedback = serializers.IntegerField()
    student_name = serializers.CharField(required=False)
    student_surname = serializers.CharField(required=False)
    group_classroom = serializers.CharField(required=False)
    group_start_date = serializers.DateField(required=False)


class GroupStudentsRequestVM(serializers.Serializer):
    """Request ViewModel for getting students by group ID"""
    group_id = serializers.IntegerField()

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value


class GroupStudentStatusUpdateVM(serializers.Serializer):
    """Group Student Status Update ViewModel"""
    student_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=StudentGroupStatus.choices)

    def validate_student_id(self, value):
        """Validate that the student exists"""
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student does not exist")
        return value

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate(self, data):
        """Validate that the group student relationship exists"""
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        
        if student_id and group_id:
            if not GroupStudent.objects.filter(student_id=student_id, group_id=group_id).exists():
                raise serializers.ValidationError("Student is not assigned to this group")
        
        return data


class GroupStudentBulkCreateVM(serializers.Serializer):
    """Bulk Group Student Creation ViewModel"""
    group_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100  # Reasonable limit
    )

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
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
        group_id = data.get('group_id')
        student_ids = data.get('student_ids', [])
        
        if group_id and student_ids:
            existing_relationships = GroupStudent.objects.filter(
                group_id=group_id,
                student_id__in=student_ids
            ).values_list('student_id', flat=True)
            
            if existing_relationships:
                raise serializers.ValidationError(
                    f"Students with IDs {list(existing_relationships)} are already assigned to this group"
                )
        
        return data


class GroupStudentBulkRemoveVM(serializers.Serializer):
    """Bulk Group Student Removal ViewModel"""
    group_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )

    def validate_group_id(self, value):
        """Validate that the group exists"""
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group does not exist")
        return value

    def validate_student_ids(self, value):
        """Validate that all students exist"""
        existing_students = Student.objects.filter(id__in=value).values_list('id', flat=True)
        missing_students = set(value) - set(existing_students)
        
        if missing_students:
            raise serializers.ValidationError(f"Students with IDs {list(missing_students)} do not exist")
        
        return value


class GroupCapacityInfoVM(serializers.Serializer):
    """Group Capacity Information ViewModel"""
    group_id = serializers.IntegerField()
    capacity = serializers.IntegerField()
    current_students = serializers.IntegerField()
    available_spots = serializers.IntegerField()
    is_full = serializers.BooleanField()
    utilization_percentage = serializers.FloatField() 