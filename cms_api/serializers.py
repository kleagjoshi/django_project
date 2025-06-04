from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from .models import (
    ApplicationUser, Course, Lecturer, Student, CourseLecturer,
    Call, StudentCall, Group, GroupStudent, Material, Payment
)

User = get_user_model()


class ApplicationUserSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationUser model"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = ApplicationUser
        fields = [
            'id', 'username', 'email', 'password', 'person_id', 'name', 'surname',
            'father_name', 'birthday', 'birth_place', 'gender', 'is_enabled',
            'created_date', 'is_active', 'is_staff'
        ]
        read_only_fields = ['id', 'created_date']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = ApplicationUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'duration', 'price', 'level', 'active'
        ]
        read_only_fields = ['id']


class LecturerSerializer(serializers.ModelSerializer):
    """Serializer for Lecturer model"""
    user_details = ApplicationUserSerializer(source='user', read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Lecturer
        fields = [
            'id', 'user_id', 'user_details', 'contract_start', 'contract_end',
            'university_degree', 'activity'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    user_details = ApplicationUserSerializer(source='user', read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'user_id', 'user_details', 'employed', 'activity',
        ]
        read_only_fields = ['id']


class CourseLecturerSerializer(serializers.ModelSerializer):
    """Serializer for CourseLecturer model"""
    course_details = CourseSerializer(source='course', read_only=True)
    lecturer_details = LecturerSerializer(source='lecturer', read_only=True)

    class Meta:
        model = CourseLecturer
        fields = [
            'id', 'course', 'lecturer', 'course_details', 'lecturer_details',
            'assigned_date'
        ]
        read_only_fields = ['id', 'assigned_date']


class CallSerializer(serializers.ModelSerializer):
    """Serializer for Call model"""
    course_details = CourseSerializer(source='course', read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = [
            'id', 'course', 'course_details', 'capacity', 'date_added',
            'application_deadline', 'applications_count'
        ]
        read_only_fields = ['id', 'date_added']

    def get_applications_count(self, obj):
        return obj.student_calls.count()


class StudentCallSerializer(serializers.ModelSerializer):
    """Serializer for StudentCall model"""
    student_details = StudentSerializer(source='student', read_only=True)
    call_details = CallSerializer(source='call', read_only=True)

    class Meta:
        model = StudentCall
        fields = [
            'id', 'student', 'call', 'student_details', 'call_details',
            'applied_date'
        ]
        read_only_fields = ['id', 'applied_date']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model"""
    course_lecturer_details = CourseLecturerSerializer(source='course_lecturer', read_only=True)
    course_name = serializers.CharField(read_only=True)
    duration = serializers.IntegerField(read_only=True)
    level = serializers.CharField(read_only=True)
    price = serializers.IntegerField(read_only=True)
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'course_lecturer', 'course_lecturer_details', 'classroom',
            'start_date', 'end_date', 'status', 'course_name',
            'duration', 'level', 'price', 'students_count'
        ]
        read_only_fields = ['id']

    def get_students_count(self, obj):
        return obj.group_students.count()


class GroupStudentSerializer(serializers.ModelSerializer):
    """Serializer for GroupStudent model"""
    group_details = GroupSerializer(source='group', read_only=True)
    student_details = StudentSerializer(source='student', read_only=True)

    class Meta:
        model = GroupStudent
        fields = [
            'id', 'group', 'student', 'group_details', 'student_details',
            'status', 'feedback'
        ]
        read_only_fields = ['id', 'enrollment_date', 'updated_at']


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Material model"""
    group_details = GroupSerializer(source='group', read_only=True)

    class Meta:
        model = Material
        fields = [
            'id', 'group', 'group_details', 'topic', 'description', 'week',
            'link'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    group_student_details = GroupStudentSerializer(source='group_student', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'group_student', 'group_student_details', 'month', 'amount',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Simplified serializers for lists/dropdowns
class CourseListSerializer(serializers.ModelSerializer):
    """Simplified Course serializer for lists"""

    class Meta:
        model = Course
        fields = ['id', 'name', 'level', 'price', 'duration']


class StudentListSerializer(serializers.ModelSerializer):
    """Simplified Student serializer for lists"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'full_name', 'user']

    def get_full_name(self, obj):
        return f"{obj.user.name} {obj.user.surname}"


class LecturerListSerializer(serializers.ModelSerializer):
    """Simplified Lecturer serializer for lists"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Lecturer
        fields = ['id', 'full_name', 'user']

    def get_full_name(self, obj):
        return f"{obj.user.name} {obj.user.surname}"


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = ApplicationUser
        fields = ('username', 'email', 'password', 'password_confirm', 'person_id', 
                 'name', 'surname', 'father_name', 'birthday', 'birth_place', 'gender')
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = ApplicationUser.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid login credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            if not user.is_enabled:
                raise serializers.ValidationError('User account is not enabled.')
        else:
            raise serializers.ValidationError('Must include username and password.')
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationUser
        fields = ('id', 'username', 'email', 'person_id', 'name', 'surname', 
                 'father_name', 'birthday', 'birth_place', 'gender', 'is_enabled',
                 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login')


class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()