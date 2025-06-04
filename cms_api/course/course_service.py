from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Course, CourseLecturer, Lecturer, Group
from cms_api.course.course_vm import (
    CourseCreateVM, CourseEditVM
)


class CourseService:
    @staticmethod
    def add_course(course_data):
        """
        Add a new course with lecturer relationships

        Args:
            course_data: Dict containing course data including lecturer_ids

        Returns:
            Course: The created course instance
        """
        # Validate input data
        serializer = CourseCreateVM(data=course_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        with transaction.atomic():
            # Create the course
            course = Course.objects.create(
                name=validated_data['name'],
                duration=validated_data['duration'],
                price=validated_data['price'],
                level=validated_data['level'],
                active=True
            )

            # Create course-lecturer relationships
            course_lecturer_list = []
            for lecturer_id in validated_data['lecturer_ids']:
                try:
                    lecturer = Lecturer.objects.get(id=lecturer_id)
                    course_lecturer = CourseLecturer(
                        course=course,
                        lecturer=lecturer
                    )
                    course_lecturer_list.append(course_lecturer)
                except Lecturer.DoesNotExist:
                    continue

            # Bulk create course-lecturer relationships
            CourseLecturer.objects.bulk_create(course_lecturer_list)

        return course

    @staticmethod
    def get_all_courses():
        """
        Get all active courses with their calls and lecturers

        Returns:
            List[dict]: List of course data in CourseVM format
        """
        courses = Course.objects.filter(active=True).prefetch_related(
            'calls',
            'course_lecturers__lecturer__user'
        )

        course_view_models = []

        for course in courses:
            # Build lecturer VMs
            course_lecturer_vms = []
            for course_lecturer in course.course_lecturers.all():
                course_lecturer_vms.append({
                    'id': course_lecturer.id,
                    'lecturer_id': course_lecturer.lecturer.id,
                    'lecturer_name': course_lecturer.lecturer.user.name
                })

            # Build call VMs
            call_base_vms = []
            for call in course.calls.all():
                call_base_vms.append({
                    'id': call.id,
                    'capacity': call.capacity
                })

            # Build course VM
            course_view_models.append({
                'id': course.id,
                'name': course.name,
                'duration': course.duration,
                'price': course.price,
                'level': course.level,
                'calls': call_base_vms,
                'lectures': course_lecturer_vms
            })

        return course_view_models

    @staticmethod
    def get_all_simple_courses():
        """
        Get all active courses in simple format (id, name only)

        Returns:
            List[dict]: List of simple course data
        """
        courses = Course.objects.filter(active=True).only('id', 'name')

        course_view_models = []
        for course in courses:
            course_view_models.append({
                'id': course.id,
                'name': course.name
            })

        return course_view_models

    @staticmethod
    def get_course_by_id(course_id):
        """
        Get a specific course by ID with full details

        Args:
            course_id: The course ID

        Returns:
            dict: Course data in CourseVM format

        Raises:
            Course.DoesNotExist: If course not found
        """
        course = get_object_or_404(
            Course.objects.prefetch_related(
                'calls',
                'course_lecturers__lecturer__user'
            ),
            id=course_id
        )

        # Build lecturer VMs
        course_lecturer_vms = []
        for course_lecturer in course.course_lecturers.all():
            course_lecturer_vms.append({
                'id': course_lecturer.id,
                'lecturer_id': course_lecturer.lecturer.id,
                'lecturer_name': course_lecturer.lecturer.user.name
            })

        # Build call VMs
        call_base_vms = []
        for call in course.calls.all():
            call_base_vms.append({
                'id': call.id,
                'capacity': call.capacity
            })

        # Build course VM
        course_view_model = {
            'id': course.id,
            'name': course.name,
            'duration': course.duration,
            'price': course.price,
            'level': course.level,
            'calls': call_base_vms,
            'lectures': course_lecturer_vms
        }

        return course_view_model

    @staticmethod
    def update_course_by_id(course_id, course_data):
        """
        Update an existing course and its lecturer relationships

        Args:
            course_id: The course ID to update
            course_data: Dict containing updated course data

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = CourseEditVM(data=course_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                course = Course.objects.get(id=course_id)

                # Update course fields
                course.name = validated_data['name']
                course.duration = validated_data['duration']
                course.price = validated_data['price']
                course.level = validated_data['level']
                course.save()

                # Remove existing lecturer relationships
                CourseLecturer.objects.filter(course_id=course_id).delete()

                # Create new lecturer relationships
                course_lecturer_list = []
                for lecturer_id in validated_data['lecturer_ids']:
                    try:
                        lecturer = Lecturer.objects.get(id=lecturer_id)
                        course_lecturer = CourseLecturer(
                            course=course,
                            lecturer=lecturer
                        )
                        course_lecturer_list.append(course_lecturer)
                    except Lecturer.DoesNotExist:
                        continue

                # Bulk create new relationships
                CourseLecturer.objects.bulk_create(course_lecturer_list)

            return True

        except Course.DoesNotExist:
            return False

    @staticmethod
    def delete_course_by_id(course_id):
        """
        Soft delete a course (set active=False) if no ongoing groups

        Args:
            course_id: The course ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            course = Course.objects.get(id=course_id)

            # Check if this course has ongoing groups
            has_ongoing_groups = Group.objects.filter(
                course_lecturer__course_id=course_id
            ).exists()

            if not has_ongoing_groups:
                course.active = False
                course.save()
                return True
            else:
                return False

        except Course.DoesNotExist:
            return False

    @staticmethod
    def get_passive_courses():
        """
        Get all inactive/deleted courses

        Returns:
            List[dict]: List of inactive course data in CourseVM format
        """
        courses = Course.objects.filter(active=False).prefetch_related(
            'calls',
            'course_lecturers__lecturer__user'
        )

        course_view_models = []

        for course in courses:
            # Build lecturer VMs
            course_lecturer_vms = []
            for course_lecturer in course.course_lecturers.all():
                course_lecturer_vms.append({
                    'id': course_lecturer.id,
                    'lecturer_id': course_lecturer.lecturer.id,
                    'lecturer_name': course_lecturer.lecturer.user.name
                })

            # Build call VMs
            call_base_vms = []
            for call in course.calls.all():
                call_base_vms.append({
                    'id': call.id,
                    'capacity': call.capacity
                })

            # Build course VM
            course_view_models.append({
                'id': course.id,
                'name': course.name,
                'duration': course.duration,
                'price': course.price,
                'level': course.level,
                'calls': call_base_vms,
                'lectures': course_lecturer_vms
            })

        return course_view_models

    @staticmethod
    def return_course(course_id):
        """
        Reactivate a soft-deleted course

        Args:
            course_id: The course ID to reactivate

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            course = Course.objects.get(id=course_id)

            if not course.active:  # Only reactivate if currently inactive
                course.active = True
                course.save()
                return True

            return False

        except Course.DoesNotExist:
            return False