from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Student, Group, GroupStudent
from cms_api.enums import StudentGroupStatus
from .group_student_vm import (
    GroupStudentCreateVM, GroupStudentRemoveVM, GroupStudentFeedbackVM,
    GroupStudentsRequestVM, GroupStudentStatusUpdateVM, GroupStudentBulkCreateVM,
    GroupStudentBulkRemoveVM
)


class GroupStudentsService:
    @staticmethod
    def get_all_students_by_group_id(group_id):
        """
        Get all students by group ID
        
        Args:
            group_id: The group ID
            
        Returns:
            List[dict]: List of student data in StudentVM format
        """
        # Validate group ID
        group_data = {'group_id': group_id}
        serializer = GroupStudentsRequestVM(data=group_data)
        serializer.is_valid(raise_exception=True)

        # Get students for the group
        group_students = GroupStudent.objects.select_related(
            'student__user'
        ).filter(group_id=group_id)

        return GroupStudentsService._build_student_view_models_from_group_students(group_students)

    @staticmethod
    def add_student_to_group(student_id, group_id):
        """
        Add student to an existing group
        
        Args:
            student_id: The student ID
            group_id: The group ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        group_student_data = {'student_id': student_id, 'group_id': group_id}
        serializer = GroupStudentCreateVM(data=group_student_data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Get group and student objects
                group = Group.objects.get(id=group_id)
                student = Student.objects.get(id=student_id)

                # Create the group student relationship with default values
                group_student = GroupStudent.objects.create(
                    status=StudentGroupStatus.UNSATISFIED,
                    group=group,
                    student=student,
                    feedback=0
                )
                
                return True

        except (Student.DoesNotExist, Group.DoesNotExist):
            return False
        except Exception:
            return False

    @staticmethod
    def remove_student_from_group(student_id, group_id):
        """
        Remove student from group
        
        Args:
            student_id: The student ID
            group_id: The group ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        group_student_data = {'student_id': student_id, 'group_id': group_id}
        serializer = GroupStudentRemoveVM(data=group_student_data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Get group, student, and group_student objects
                group = Group.objects.get(id=group_id)
                student = Student.objects.get(id=student_id)
                group_student = GroupStudent.objects.get(
                    group_id=group_id,
                    student_id=student_id
                )

                # Remove the relationship
                group_student.delete()
                return True

        except (Student.DoesNotExist, Group.DoesNotExist, GroupStudent.DoesNotExist):
            return False

    @staticmethod
    def update_feedback(student_id, group_id, feedback):
        """
        Update feedback for a student in a group
        
        Args:
            student_id: The student ID
            group_id: The group ID
            feedback: The feedback value
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        feedback_data = {
            'student_id': student_id,
            'group_id': group_id,
            'feedback': feedback
        }
        serializer = GroupStudentFeedbackVM(data=feedback_data)
        serializer.is_valid(raise_exception=True)

        try:
            group_student = GroupStudent.objects.get(
                student_id=student_id,
                group_id=group_id
            )
            
            group_student.feedback = feedback
            group_student.save()
            return True

        except GroupStudent.DoesNotExist:
            return False

    @staticmethod
    def get_all_group_students():
        """
        Get all group student relationships
        
        Returns:
            List[dict]: List of group student data
        """
        group_students = GroupStudent.objects.select_related('student__user', 'group').all()
        return GroupStudentsService._build_group_student_view_models(group_students)

    @staticmethod
    def get_groups_by_student_id(student_id):
        """
        Get all groups for a specific student
        
        Args:
            student_id: The student ID
            
        Returns:
            List[dict]: List of group data for the student
        """
        group_students = GroupStudent.objects.select_related('group').filter(student_id=student_id)
        return GroupStudentsService._build_group_view_models_from_group_students(group_students)

    @staticmethod
    def update_student_status(student_id, group_id, status):
        """
        Update student status in group
        
        Args:
            student_id: The student ID
            group_id: The group ID
            status: The new status
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        status_data = {
            'student_id': student_id,
            'group_id': group_id,
            'status': status
        }
        serializer = GroupStudentStatusUpdateVM(data=status_data)
        serializer.is_valid(raise_exception=True)

        try:
            group_student = GroupStudent.objects.get(
                student_id=student_id,
                group_id=group_id
            )
            
            group_student.status = status
            group_student.save()
            return True

        except GroupStudent.DoesNotExist:
            return False

    @staticmethod
    def add_bulk_students_to_group(group_id, student_ids):
        """
        Add multiple students to a group
        
        Args:
            group_id: The group ID
            student_ids: List of student IDs
            
        Returns:
            dict: Result with success status and details
        """
        # Validate input data
        bulk_data = {'group_id': group_id, 'student_ids': student_ids}
        serializer = GroupStudentBulkCreateVM(data=bulk_data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                group = Group.objects.get(id=group_id)
                students = Student.objects.filter(id__in=student_ids)

                group_students = []
                for student in students:
                    group_students.append(GroupStudent(
                        group=group,
                        student=student,
                        status=StudentGroupStatus.PENDING,
                        feedback=0
                    ))

                # Bulk create the relationships
                GroupStudent.objects.bulk_create(group_students)

                return {
                    'success': True,
                    'created_count': len(group_students),
                    'message': f'Successfully added {len(group_students)} students to group'
                }

        except Exception as e:
            return {
                'success': False,
                'created_count': 0,
                'message': f'Failed to add students to group: {str(e)}'
            }

    @staticmethod
    def remove_bulk_students_from_group(group_id, student_ids):
        """
        Remove multiple students from a group
        
        Args:
            group_id: The group ID
            student_ids: List of student IDs
            
        Returns:
            dict: Result with success status and details
        """
        # Validate input data
        bulk_data = {'group_id': group_id, 'student_ids': student_ids}
        serializer = GroupStudentBulkRemoveVM(data=bulk_data)
        serializer.is_valid(raise_exception=True)

        try:
            # Get existing relationships
            group_students = GroupStudent.objects.filter(
                group_id=group_id,
                student_id__in=student_ids
            )

            deleted_count = group_students.count()
            group_students.delete()

            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'Successfully removed {deleted_count} students from group'
            }

        except Exception as e:
            return {
                'success': False,
                'deleted_count': 0,
                'message': f'Failed to remove students from group: {str(e)}'
            }

    @staticmethod
    def get_group_capacity_info(group_id):
        """
        Get group capacity information
        
        Args:
            group_id: The group ID
            
        Returns:
            dict: Group capacity information (without capacity field since Group model doesn't have it)
        """
        try:
            group = Group.objects.get(id=group_id)
            current_students = GroupStudent.objects.filter(group_id=group_id).count()

            return {
                'group_id': group_id,
                'current_students': current_students,
                'note': 'Group capacity information not available - Group model does not have capacity field'
            }

        except Group.DoesNotExist:
            return None

    @staticmethod
    def get_group_students_statistics():
        """
        Get group student statistics
        
        Returns:
            dict: Group student statistics
        """
        total_relationships = GroupStudent.objects.count()
        total_students_with_groups = GroupStudent.objects.values('student_id').distinct().count()
        total_groups_with_students = GroupStudent.objects.values('group_id').distinct().count()
        
        # Students without any groups
        total_students = Student.objects.filter(activity=True).count()
        students_without_groups = total_students - total_students_with_groups
        
        # Groups without any students
        total_groups = Group.objects.count()
        groups_without_students = total_groups - total_groups_with_students

        return {
            'total_group_student_relationships': total_relationships,
            'total_students_with_groups': total_students_with_groups,
            'total_groups_with_students': total_groups_with_students,
            'students_without_groups': students_without_groups,
            'groups_without_students': groups_without_students,
            'average_students_per_group': round(total_relationships / total_groups_with_students, 2) if total_groups_with_students > 0 else 0,
            'average_groups_per_student': round(total_relationships / total_students_with_groups, 2) if total_students_with_groups > 0 else 0
        }

    @staticmethod
    def check_group_student_exists(student_id, group_id):
        """
        Check if a group student relationship exists
        
        Args:
            student_id: The student ID
            group_id: The group ID
            
        Returns:
            bool: True if relationship exists, False otherwise
        """
        return GroupStudent.objects.filter(student_id=student_id, group_id=group_id).exists()

    @staticmethod
    def get_student_feedback_in_group(student_id, group_id):
        """
        Get student feedback in a specific group
        
        Args:
            student_id: The student ID
            group_id: The group ID
            
        Returns:
            int or None: Feedback value or None if not found
        """
        try:
            group_student = GroupStudent.objects.get(student_id=student_id, group_id=group_id)
            return group_student.feedback
        except GroupStudent.DoesNotExist:
            return None

    @staticmethod
    def _build_student_view_models_from_group_students(group_students):
        """
        Helper method to build student view models from group students
        
        Args:
            group_students: QuerySet of GroupStudent objects
            
        Returns:
            List[dict]: List of student data in StudentVM format with group_student_id
        """
        student_view_models = []

        for group_student in group_students:
            student = group_student.student
            user = student.user

            student_view_models.append({
                'id': student.id,
                'person_id': user.person_id or '',
                'name': user.name,
                'surname': user.surname,
                'father_name': user.father_name or '',
                'birthday': user.birthday,
                'birth_place': user.birth_place or '',
                'gender': user.gender or '',
                'employed': student.employed,
                'user_id': str(user.id),
                'group_student_id': group_student.id
            })

        return student_view_models

    @staticmethod
    def _build_group_student_view_models(group_students):
        """
        Helper method to build group student view models
        
        Args:
            group_students: QuerySet of GroupStudent objects
            
        Returns:
            List[dict]: List of group student data
        """
        group_student_view_models = []

        for group_student in group_students:
            group_student_view_models.append({
                'id': group_student.id,
                'student_id': group_student.student.id,
                'group_id': group_student.group.id,
                'status': group_student.status,
                'feedback': group_student.feedback,
                'student_name': group_student.student.user.name,
                'student_surname': group_student.student.user.surname,
                'group_classroom': group_student.group.classroom,
                'group_start_date': group_student.group.start_date
            })

        return group_student_view_models

    @staticmethod
    def _build_group_view_models_from_group_students(group_students):
        """
        Helper method to build group view models from group students
        
        Args:
            group_students: QuerySet of GroupStudent objects
            
        Returns:
            List[dict]: List of group data
        """
        group_view_models = []

        for group_student in group_students:
            group = group_student.group

            group_view_models.append({
                'id': group.id,
                'classroom': group.classroom,
                'start_date': group.start_date,
                'end_date': group.end_date,
                'status': group.status,
                'course_lecturer_id': group.course_lecturer_id
            })

        return group_view_models 