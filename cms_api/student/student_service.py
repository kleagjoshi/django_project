from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from cms_api.models import Student, ApplicationUser, GroupStudent
from cms_api.enums import StudentGroupStatus
from .student_vm import (
    StudentCreateVM, StudentEditVM, StudentVM, StudentSimpleVM,
    StudentSearchVM, StudentStatusUpdateVM, StudentReturnVM
)


class StudentService:
    @staticmethod
    def create_student(student_data):
        """
        Create a new student

        Args:
            student_data: Dict containing student creation data

        Returns:
            dict: Created student data or None if failed
        """
        # Validate input data
        serializer = StudentCreateVM(data=student_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                student = Student.objects.create(
                    user_id=validated_data['user_id'],
                    employed=validated_data['employed'],
                    activity=True
                )
                return StudentService.get_student_by_id(student.id)

        except Exception as e:
            raise Exception(f"Failed to create student: {str(e)}")

    @staticmethod
    def delete_student(student_id):
        """
        Soft delete a student (set Activity=false and User.IsEnabled=false)

        Args:
            student_id: The student ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            student = Student.objects.select_related('user').get(id=student_id)
            student.activity = False
            student.user.is_enabled = False
            student.save()
            student.user.save()
            return True

        except Student.DoesNotExist:
            return False

    @staticmethod
    def edit_student(student_id, student_data):
        """
        Edit an existing student

        Args:
            student_id: The student ID to edit
            student_data: Dict containing updated student data

        Returns:
            dict: Updated student data or None if failed
        """
        # Validate input data
        serializer = StudentEditVM(data=student_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                student = Student.objects.select_related('user').get(id=student_id)

                # Update user fields
                user = student.user
                user.person_id = validated_data.get('person_id', user.person_id)
                user.name = validated_data['name']
                user.surname = validated_data['surname']
                user.father_name = validated_data.get('father_name', user.father_name)
                user.birthday = validated_data.get('birthday', user.birthday)
                user.birth_place = validated_data.get('birth_place', user.birth_place)
                user.gender = validated_data.get('gender', user.gender)
                user.save()

                # Update student fields
                student.employed = validated_data['employed']
                student.save()

                return StudentService.get_student_by_id(student_id)

        except Student.DoesNotExist:
            return None

    @staticmethod
    def get_simple_students():
        """
        Get all students in simple format for dropdowns

        Returns:
            List[dict]: List of simple student data
        """
        students = Student.objects.select_related('user').filter(activity=True)
        return StudentService._build_simple_student_view_models(students)

    @staticmethod
    def get_all_student_details():
        """
        Get all active students with full details

        Returns:
            List[dict]: List of student data in StudentVM format
        """
        students = Student.objects.select_related('user').filter(activity=True)
        return StudentService._build_student_view_models(students, include_is_enabled=True)

    @staticmethod
    def get_all_passive_students():
        """
        Get all inactive students

        Returns:
            List[dict]: List of passive student data
        """
        students = Student.objects.select_related('user').filter(activity=False)
        return StudentService._build_student_view_models(students, include_is_enabled=False)

    @staticmethod
    def get_student_by_id(student_id):
        """
        Get a specific student by ID

        Args:
            student_id: The student ID

        Returns:
            dict: Student data in StudentVM format or None if not found
        """
        try:
            student = Student.objects.select_related('user').get(id=student_id)
            students = [student]
            student_view_models = StudentService._build_student_view_models(students, include_is_enabled=False)
            return student_view_models[0] if student_view_models else None

        except Student.DoesNotExist:
            return None

    @staticmethod
    def search_student(name, surname):
        """
        Search for students by name and surname

        Args:
            name: Student name (optional)
            surname: Student surname (optional)

        Returns:
            List[dict]: List of matching student data
        """
        # Validate search parameters
        search_data = {'name': name or '', 'surname': surname or ''}
        serializer = StudentSearchVM(data=search_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Build query
        query = Q(activity=True)

        if validated_data['name']:
            query &= Q(user__name__icontains=validated_data['name'])

        if validated_data['surname']:
            query &= Q(user__surname__icontains=validated_data['surname'])

        students = Student.objects.select_related('user').filter(query)
        return StudentService._build_student_view_models(students, include_is_enabled=False)

    @staticmethod
    def return_student(student_id):
        """
        Reactivate a soft-deleted student

        Args:
            student_id: The student ID to reactivate

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            student = Student.objects.select_related('user').get(id=student_id)

            # Only reactivate if currently inactive
            if not student.activity:
                student.activity = True
                student.user.is_enabled = True
                student.save()
                student.user.save()
                return True

            return False  # Student is already active

        except Student.DoesNotExist:
            return False

    @staticmethod
    def update_student_status(student_id, new_status):
        """
        Update student status in group

        Args:
            student_id: The student ID
            new_status: The new StudentGroupStatus

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        status_data = {'student_id': student_id, 'new_status': new_status}
        serializer = StudentStatusUpdateVM(data=status_data)
        serializer.is_valid(raise_exception=True)

        try:
            # Get the first group student record
            group_student = GroupStudent.objects.select_related('student').filter(
                student_id=student_id
            ).first()

            if group_student:
                group_student.status = new_status
                group_student.save()
                return True

            return False

        except Exception:
            return False

    @staticmethod
    def get_all_students():
        """
        Get all students (both active and inactive)

        Returns:
            List[dict]: List of all student data
        """
        students = Student.objects.select_related('user').all()
        return StudentService._build_student_view_models(students, include_is_enabled=True)

    @staticmethod
    def get_students_statistics():
        """
        Get student statistics

        Returns:
            dict: Student statistics
        """
        all_students = Student.objects.all()

        if not all_students.exists():
            return {
                'total_students': 0,
                'active_students': 0,
                'inactive_students': 0,
                'employed_students': 0,
                'unemployed_students': 0,
                'students_with_groups': 0,
                'students_without_groups': 0
            }

        active_students = all_students.filter(activity=True)
        inactive_students = all_students.filter(activity=False)
        employed_students = all_students.filter(employed=True)
        unemployed_students = all_students.filter(employed=False)

        # Students with group assignments
        students_with_groups = Student.objects.filter(
            id__in=GroupStudent.objects.values_list('student_id', flat=True)
        ).count()

        students_without_groups = all_students.count() - students_with_groups

        return {
            'total_students': all_students.count(),
            'active_students': active_students.count(),
            'inactive_students': inactive_students.count(),
            'employed_students': employed_students.count(),
            'unemployed_students': unemployed_students.count(),
            'students_with_groups': students_with_groups,
            'students_without_groups': students_without_groups
        }

    @staticmethod
    def get_students_by_employment_status(employed):
        """
        Get students by employment status

        Args:
            employed: Boolean indicating employment status

        Returns:
            List[dict]: List of student data
        """
        students = Student.objects.select_related('user').filter(
            activity=True,
            employed=employed
        )
        return StudentService._build_student_view_models(students, include_is_enabled=True)

    @staticmethod
    def _build_student_view_models(students, include_is_enabled=False):
        """
        Helper method to build student view models from queryset

        Args:
            students: QuerySet of Student objects
            include_is_enabled: Whether to include is_enabled field

        Returns:
            List[dict]: List of student data in StudentVM format
        """
        student_view_models = []

        for student in students:
            student_data = {
                'id': student.id,
                'person_id': student.user.person_id or '',
                'name': student.user.name,
                'surname': student.user.surname,
                'father_name': student.user.father_name or '',
                'birthday': student.user.birthday,
                'birth_place': student.user.birth_place or '',
                'gender': student.user.gender or '',
                'employed': student.employed,
                'user_id': str(student.user.id)
            }

            if include_is_enabled:
                student_data['is_enabled'] = student.user.is_enabled

            student_view_models.append(student_data)

        return student_view_models

    @staticmethod
    def _build_simple_student_view_models(students):
        """
        Helper method to build simple student view models from queryset

        Args:
            students: QuerySet of Student objects

        Returns:
            List[dict]: List of simple student data
        """
        simple_student_view_models = []

        for student in students:
            simple_student_view_models.append({
                'id': student.id,
                'user_id': str(student.user.id),
                'name': student.user.name,
                'surname': student.user.surname
            })

        return simple_student_view_models