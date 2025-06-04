from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from cms_api.models import Lecturer, Course, ApplicationUser, CourseLecturer, Group
from .lecturer_vm import (
    LecturerCreateVM, LecturerEditVM, LecturerVM, LecturerSimpleVM,
    CourseOfLecturerVM, LecturerSearchVM
)


class LecturersService:
    @staticmethod
    def add_lecturer(lecturer_data):
        """
        Add a new lecturer with course relationships

        Args:
            lecturer_data: Dict containing lecturer data including course_ids

        Returns:
            bool: True if successful, False if lecturer already exists
        """
        # Validate input data
        serializer = LecturerCreateVM(data=lecturer_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Check if this lecturer is already added
        existing_lecturer = Lecturer.objects.filter(
            user_id=validated_data['user_id']
        ).first()

        if existing_lecturer is not None:
            return False

        with transaction.atomic():
            # Get the user
            user = get_object_or_404(ApplicationUser, id=validated_data['user_id'])

            # Create the lecturer
            lecturer = Lecturer.objects.create(
                contract_start=validated_data['contract_start'],
                contract_end=validated_data['contract_end'],
                university_degree=validated_data['university_degree'],
                activity=True,
                user=user
            )

            # Create course-lecturer relationships
            course_lecturer_list = []
            for course_id in validated_data.get('course_ids', []):
                try:
                    course = Course.objects.get(id=course_id)
                    course_lecturer = CourseLecturer(
                        course=course,
                        lecturer=lecturer
                    )
                    course_lecturer_list.append(course_lecturer)
                except Course.DoesNotExist:
                    continue

            # Bulk create course-lecturer relationships
            CourseLecturer.objects.bulk_create(course_lecturer_list)

        return True

    @staticmethod
    def get_all_lecturers():
        """
        Get all active lecturers with their user and course information

        Returns:
            List[dict]: List of lecturer data in LecturerVM format
        """
        lecturers = Lecturer.objects.filter(activity=True).select_related(
            'user'
        ).prefetch_related(
            'course_lecturers__course'
        ).all()

        return LecturersService._build_lecturer_view_models(lecturers)

    @staticmethod
    def get_all_passive_lecturers():
        """
        Get all inactive lecturers

        Returns:
            List[dict]: List of inactive lecturer data in LecturerVM format
        """
        lecturers = Lecturer.objects.filter(activity=False).select_related(
            'user'
        ).prefetch_related(
            'course_lecturers__course'
        ).all()

        return LecturersService._build_lecturer_view_models(lecturers)

    @staticmethod
    def get_lecturer_by_id(lecturer_id):
        """
        Get a specific lecturer by ID with full details

        Args:
            lecturer_id: The lecturer ID

        Returns:
            dict: Lecturer data in LecturerVM format or None if not found
        """
        try:
            lecturer = Lecturer.objects.select_related(
                'user'
            ).prefetch_related(
                'course_lecturers__course'
            ).get(id=lecturer_id)

            lecturer_view_models = LecturersService._build_lecturer_view_models([lecturer])
            return lecturer_view_models[0] if lecturer_view_models else None

        except Lecturer.DoesNotExist:
            return None

    @staticmethod
    def get_all_simple_lecturers():
        """
        Get all active lecturers in simple format for forms

        Returns:
            List[dict]: List of simple lecturer data
        """
        lecturers = Lecturer.objects.filter(activity=True).select_related('user').all()

        lecturer_view_models = []
        for lecturer in lecturers:
            lecturer_view_models.append({
                'id': lecturer.id,
                'user_id': lecturer.user_id,
                'name': lecturer.user.name,
                'surname': lecturer.user.surname
            })

        return lecturer_view_models

    @staticmethod
    def update_lecturer_by_id(lecturer_id, lecturer_data):
        """
        Update an existing lecturer

        Args:
            lecturer_id: The lecturer ID to update
            lecturer_data: Dict containing updated lecturer data

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = LecturerEditVM(data=lecturer_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                lecturer = Lecturer.objects.select_related('user').get(id=lecturer_id)

                # Update user information
                lecturer.user.person_id = validated_data['person_id']
                lecturer.user.name = validated_data['name']
                lecturer.user.surname = validated_data['surname']
                lecturer.user.father_name = validated_data['father_name']
                lecturer.user.birthday = validated_data['birthday']
                lecturer.user.birth_place = validated_data['birth_place']
                lecturer.user.gender = validated_data['gender']
                lecturer.user.save()

                # Update lecturer information
                lecturer.contract_start = validated_data['contract_start']
                lecturer.contract_end = validated_data['contract_end']
                lecturer.university_degree = validated_data['university_degree']
                lecturer.save()

                # Remove existing course relations
                CourseLecturer.objects.filter(lecturer_id=lecturer_id).delete()

                # Update course relations
                course_lecturer_list = []
                for course_id in validated_data.get('course_ids', []):
                    try:
                        course = Course.objects.get(id=course_id)
                        course_lecturer = CourseLecturer(
                            course=course,
                            lecturer=lecturer
                        )
                        course_lecturer_list.append(course_lecturer)
                    except Course.DoesNotExist:
                        continue

                # Bulk create new course-lecturer relationships
                CourseLecturer.objects.bulk_create(course_lecturer_list)

            return True

        except Lecturer.DoesNotExist:
            return False

    @staticmethod
    def delete_lecturer_by_id(lecturer_id):
        """
        Soft delete a lecturer (set activity to false)

        Args:
            lecturer_id: The lecturer ID to delete

        Returns:
            bool: True if successful, False if lecturer has ongoing groups or not found
        """
        try:
            lecturer = Lecturer.objects.select_related('user').get(id=lecturer_id)

            # Check if this lecturer has ongoing groups
            has_ongoing_groups = Group.objects.filter(
                course_lecturer__lecturer_id=lecturer_id
            ).exists()

            if not has_ongoing_groups:
                lecturer.activity = False
                lecturer.user.is_enabled = False
                lecturer.save()
                lecturer.user.save()
                return True
            else:
                return False

        except Lecturer.DoesNotExist:
            return False

    @staticmethod
    def return_lecturer(lecturer_id):
        """
        Reactivate a soft-deleted lecturer

        Args:
            lecturer_id: The lecturer ID to reactivate

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            lecturer = Lecturer.objects.select_related('user').get(id=lecturer_id)

            if not lecturer.activity:
                lecturer.activity = True
                lecturer.user.is_enabled = True
                lecturer.save()
                lecturer.user.save()
                return True

            return False

        except Lecturer.DoesNotExist:
            return False

    @staticmethod
    def search_lecturer(name=None, surname=None):
        """
        Search lecturers by name and surname

        Args:
            name: Name to search for (optional)
            surname: Surname to search for (optional)

        Returns:
            List[dict]: List of matching lecturer data in LecturerVM format
        """
        # Build query
        query = Q(activity=True)

        if name:
            query &= Q(user__name__icontains=name)
        if surname:
            query &= Q(user__surname__icontains=surname)

        lecturers = Lecturer.objects.filter(query).select_related(
            'user'
        ).prefetch_related(
            'course_lecturers__course'
        ).all()

        return LecturersService._build_lecturer_view_models(lecturers)

    @staticmethod
    def _build_lecturer_view_models(lecturers):
        """
        Helper method to build lecturer view models from queryset

        Args:
            lecturers: QuerySet of Lecturer objects

        Returns:
            List[dict]: List of lecturer data in LecturerVM format
        """
        lecturer_view_models = []

        for lecturer in lecturers:
            # Build course VMs
            course_lecturer_vms = []
            for course_lecturer in lecturer.course_lecturers.all():
                course_lecturer_vms.append({
                    'id': course_lecturer.id,
                    'course_name': course_lecturer.course.name,
                    'course_id': course_lecturer.course.id
                })

            # Build lecturer VM
            lecturer_view_models.append({
                'id': lecturer.id,
                'person_id': lecturer.user.person_id,
                'name': lecturer.user.name,
                'surname': lecturer.user.surname,
                'father_name': lecturer.user.father_name,
                'birthday': lecturer.user.birthday,
                'birth_place': lecturer.user.birth_place,
                'gender': lecturer.user.gender,
                'contract_start': lecturer.contract_start,
                'contract_end': lecturer.contract_end,
                'university_degree': lecturer.university_degree,
                'user_id': lecturer.user_id,
                'courses': course_lecturer_vms
            })

        return lecturer_view_models