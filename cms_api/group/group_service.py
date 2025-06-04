from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Group, CourseLecturer, Student, GroupStudent, Course
from cms_api.enums import GroupStatus, StudentGroupStatus
from .group_vm import (
    GroupCreateVM, GroupEditVM, GroupGetVM, GroupSimpleVM,
    CourseLecturerGroupVM, GroupStudentSimpleVM
)


class GroupsService:
    @staticmethod
    def add_group(group_data):
        """
        Add a new group with students

        Args:
            group_data: Dict containing group data including student_ids

        Returns:
            Group: The created group instance
        """
        # Validate input data
        serializer = GroupCreateVM(data=group_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        with transaction.atomic():
            # Get the course lecturer
            course_lecturer = get_object_or_404(
                CourseLecturer,
                id=validated_data['course_lecturer_id']
            )

            # Calculate end_date from start_date + duration
            from datetime import timedelta
            start_date = validated_data['start_date']
            duration_days = validated_data['duration']
            end_date = start_date + timedelta(days=duration_days)

            # Create the group
            group = Group.objects.create(
                classroom=validated_data['classroom'],
                start_date=start_date,
                end_date=end_date,
                course_lecturer=course_lecturer,
                status=GroupStatus.ONGOING  # Default status (equivalent to 0)
            )

            # Create group-student relationships
            group_student_list = []
            for student_id in validated_data.get('student_ids', []):
                try:
                    student = Student.objects.get(id=student_id)
                    group_student = GroupStudent(
                        feedback=0,
                        status=StudentGroupStatus.UNSATISFIED,  # Default status (equivalent to 0)
                        group=group,
                        student=student
                    )
                    group_student_list.append(group_student)
                except Student.DoesNotExist:
                    continue

            # Bulk create group-student relationships
            GroupStudent.objects.bulk_create(group_student_list)

        return group

    @staticmethod
    def update_group_by_id(group_id, group_data):
        """
        Update an existing group

        Args:
            group_id: The group ID to update
            group_data: Dict containing updated group data

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = GroupEditVM(data=group_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            group = Group.objects.get(id=group_id)
            group.classroom = validated_data['classroom']
            group.save()
            return True

        except Group.DoesNotExist:
            return False

    @staticmethod
    def get_all_groups():
        """
        Get all groups with their course lecturer and student information

        Returns:
            List[dict]: List of group data in GroupGetVM format
        """
        groups = Group.objects.select_related(
            'course_lecturer__course',
            'course_lecturer__lecturer__user'
        ).prefetch_related(
            'group_students__student__user'
        ).all()

        return GroupsService._build_group_view_models(groups)

    @staticmethod
    def get_group_by_id(group_id):
        """
        Get a specific group by ID with full details

        Args:
            group_id: The group ID

        Returns:
            dict: Group data in GroupGetVM format

        Raises:
            Group.DoesNotExist: If group not found
        """
        group = get_object_or_404(
            Group.objects.select_related(
                'course_lecturer__course',
                'course_lecturer__lecturer__user'
            ).prefetch_related(
                'group_students__student__user'
            ),
            id=group_id
        )

        group_view_models = GroupsService._build_group_view_models([group])
        return group_view_models[0] if group_view_models else None

    @staticmethod
    def get_all_groups_by_status(status):
        """
        Get all groups filtered by status

        Args:
            status: GroupStatus enum value

        Returns:
            List[dict]: List of group data in GroupGetVM format
        """
        groups = Group.objects.filter(status=status).select_related(
            'course_lecturer__course',
            'course_lecturer__lecturer__user'
        ).prefetch_related(
            'group_students__student__user'
        ).all()

        return GroupsService._build_group_view_models(groups)

    @staticmethod
    def get_all_groups_by_lecturer_id(lecturer_id):
        """
        Get all groups for a specific lecturer

        Args:
            lecturer_id: The lecturer ID

        Returns:
            List[dict]: List of group data in GroupGetVM format
        """
        groups = Group.objects.filter(
            course_lecturer__lecturer_id=lecturer_id
        ).select_related(
            'course_lecturer__course',
            'course_lecturer__lecturer__user'
        ).prefetch_related(
            'group_students__student__user'
        ).all()

        return GroupsService._build_group_view_models(groups)

    @staticmethod
    def get_all_groups_by_student_id(student_id):
        """
        Get all groups for a specific student

        Args:
            student_id: The student ID

        Returns:
            List[dict]: List of group data in GroupGetVM format
        """
        groups = Group.objects.filter(
            group_students__student_id=student_id
        ).select_related(
            'course_lecturer__course',
            'course_lecturer__lecturer__user'
        ).prefetch_related(
            'group_students__student__user'
        ).distinct()

        return GroupsService._build_group_view_models(groups)

    @staticmethod
    def update_status(group_id):
        """
        Update group status to FINISHED

        Args:
            group_id: The group ID to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            group = Group.objects.get(id=group_id)
            group.status = GroupStatus.ACTIVE  # Status = 1 equivalent
            group.save()
            return True

        except Group.DoesNotExist:
            return False

    @staticmethod
    def get_all_course_lecturers():
        """
        Get all course lecturers

        Returns:
            List[dict]: List of course lecturer data in CourseLecturerGroupVM format
        """
        course_lecturers = CourseLecturer.objects.select_related(
            'course',
            'lecturer__user'
        ).all()

        course_lecturer_view_models = []
        for course_lecturer in course_lecturers:
            course_lecturer_view_models.append({
                'id': course_lecturer.id,
                'lecturer_name': course_lecturer.lecturer.user.name,
                'lecturer_id': course_lecturer.lecturer.id,
                'course_name': course_lecturer.course.name,
                'course_id': course_lecturer.course.id
            })

        return course_lecturer_view_models

    @staticmethod
    def _build_group_view_models(groups):
        """
        Helper method to build group view models from queryset

        Args:
            groups: QuerySet of Group objects

        Returns:
            List[dict]: List of group data in GroupGetVM format
        """
        group_view_models = []

        for group in groups:
            # Build course lecturer VM
            course_lecturer_vm = {
                'id': group.course_lecturer.id,
                'course_id': group.course_lecturer.course.id,
                'course_name': group.course_lecturer.course.name,
                'lecturer_id': group.course_lecturer.lecturer.id,
                'lecturer_name': group.course_lecturer.lecturer.user.name
            }

            # Build student VMs
            student_vms = []
            for group_student in group.group_students.all():
                student_vms.append({
                    'id': group_student.student.id,
                    'user_id': group_student.student.user_id,
                    'name': group_student.student.user.name,
                    'surname': group_student.student.user.surname
                })

            # Build group VM
            group_view_models.append({
                'id': group.id,
                'classroom': group.classroom,
                'start_date': group.start_date,
                'end_date': group.end_date,
                'duration': (group.end_date.date() - group.start_date.date()).days if group.end_date and group.start_date else None,
                'status': group.status,
                'course_lecturer_id': group.course_lecturer.id,
                'course_lecturer': course_lecturer_vm,
                'students': student_vms
            })

        return group_view_models

    @staticmethod
    def get_simple_groups():
        """
        Get all groups in simple format

        Returns:
            List[dict]: List of simple group data
        """
        groups = Group.objects.select_related(
            'course_lecturer__course',
            'course_lecturer__lecturer__user'
        ).all()

        group_view_models = []
        for group in groups:
            group_view_models.append({
                'id': group.id,
                'classroom': group.classroom,
                'course_name': group.course_lecturer.course.name,
                'lecturer_name': group.course_lecturer.lecturer.user.name,
                'status': group.status
            })

        return group_view_models