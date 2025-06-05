from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Student, Call, StudentCall
from .student_call_vm import (
    StudentCallCreateVM, StudentCallDeleteVM, StudentCallVM,
    CallStudentsRequestVM, StudentCallBulkCreateVM, StudentCallBulkDeleteVM
)


class StudentCallsService:
    @staticmethod
    def add_student_call(student_id, call_id):
        """
        Add a student call connection

        Args:
            student_id: The student ID
            call_id: The call ID

        Returns:
            dict: Result with success status and message
        """
        try:
            with transaction.atomic():
                # Basic existence validation
                try:
                    student = Student.objects.get(id=student_id)
                except Student.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Student not found'
                    }
                
                try:
                    call = Call.objects.get(id=call_id)
                except Call.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Call not found'
                    }

                # Check if student is already registered for this call
                if StudentCall.objects.filter(student_id=student_id, call_id=call_id).exists():
                    return {
                        'success': False,
                        'message': 'Student is already registered for this call'
                    }

                # Check if call has capacity
                current_students = StudentCall.objects.filter(call_id=call_id).count()
                if current_students >= call.capacity:
                    return {
                        'success': False,
                        'message': f'Call has reached its maximum capacity of {call.capacity} students'
                    }

                # Create the student call relationship
                student_call = StudentCall.objects.create(
                    student=student,
                    call=call
                )

                return {
                    'success': True,
                    'message': 'Student successfully added to call'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to add student to call: {str(e)}'
            }

    @staticmethod
    def delete_student_call(student_id, call_id):
        """
        Delete a student call connection

        Args:
            student_id: The student ID
            call_id: The call ID

        Returns:
            dict: Result with success status and message
        """
        try:
            student_call = StudentCall.objects.get(
                student_id=student_id,
                call_id=call_id
            )
            student_call.delete()
            return {
                'success': True,
                'message': 'Student successfully removed from call'
            }

        except StudentCall.DoesNotExist:
            return {
                'success': False,
                'message': 'Student call relationship not found'
            }

    @staticmethod
    def get_all_students_by_call_id(call_id):
        """
        Get all students by call ID

        Args:
            call_id: The call ID

        Returns:
            List[dict]: List of student data in StudentVM format
        """
        # Validate call ID
        call_data = {'call_id': call_id}
        serializer = CallStudentsRequestVM(data=call_data)
        serializer.is_valid(raise_exception=True)

        # Get students for the call
        student_calls = StudentCall.objects.select_related(
            'student__user'
        ).filter(call_id=call_id)

        return StudentCallsService._build_student_view_models_from_calls(student_calls)

    @staticmethod
    def get_all_student_calls():
        """
        Get all student call relationships

        Returns:
            List[dict]: List of student call data
        """
        student_calls = StudentCall.objects.select_related('student__user', 'call').all()
        return StudentCallsService._build_student_call_view_models(student_calls)

    @staticmethod
    def get_student_calls_by_student_id(student_id):
        """
        Get all calls for a specific student

        Args:
            student_id: The student ID

        Returns:
            List[dict]: List of call data for the student
        """
        student_calls = StudentCall.objects.select_related('call').filter(student_id=student_id)
        return StudentCallsService._build_call_view_models_from_student_calls(student_calls)

    @staticmethod
    def add_bulk_student_calls(call_id, student_ids):
        """
        Add multiple students to a call

        Args:
            call_id: The call ID
            student_ids: List of student IDs

        Returns:
            dict: Result with success status and details
        """
        # Validate input data
        bulk_data = {'call_id': call_id, 'student_ids': student_ids}
        serializer = StudentCallBulkCreateVM(data=bulk_data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                call = Call.objects.get(id=call_id)
                
                # Check current capacity
                current_students = StudentCall.objects.filter(call_id=call_id).count()
                available_spots = call.capacity - current_students
                
                if available_spots <= 0:
                    return {
                        'success': False,
                        'created_count': 0,
                        'message': f'Call has reached its maximum capacity of {call.capacity} students'
                    }
                
                # Get valid students (exist and not already registered)
                existing_student_calls = StudentCall.objects.filter(
                    call_id=call_id,
                    student_id__in=student_ids
                ).values_list('student_id', flat=True)
                
                valid_student_ids = [sid for sid in student_ids if sid not in existing_student_calls]
                students = Student.objects.filter(id__in=valid_student_ids)
                
                # Limit to available spots
                students_to_add = list(students)[:available_spots]
                
                if not students_to_add:
                    return {
                        'success': False,
                        'created_count': 0,
                        'message': 'No valid students to add (either already registered or not found)'
                    }

                student_calls = []
                for student in students_to_add:
                    student_calls.append(StudentCall(student=student, call=call))

                # Bulk create the relationships
                StudentCall.objects.bulk_create(student_calls)
                
                message = f'Successfully added {len(student_calls)} students to call'
                if len(students_to_add) < len(student_ids):
                    skipped_count = len(student_ids) - len(students_to_add)
                    if available_spots < len(valid_student_ids):
                        message += f' (limited by capacity, {skipped_count} students not added)'
                    else:
                        message += f' ({skipped_count} students were already registered or not found)'

                return {
                    'success': True,
                    'created_count': len(student_calls),
                    'message': message
                }

        except Call.DoesNotExist:
            return {
                'success': False,
                'created_count': 0,
                'message': 'Call not found'
            }
        except Exception as e:
            return {
                'success': False,
                'created_count': 0,
                'message': f'Failed to add students to call: {str(e)}'
            }

    @staticmethod
    def delete_bulk_student_calls(call_id, student_ids):
        """
        Remove multiple students from a call

        Args:
            call_id: The call ID
            student_ids: List of student IDs

        Returns:
            dict: Result with success status and details
        """
        # Validate input data
        bulk_data = {'call_id': call_id, 'student_ids': student_ids}
        serializer = StudentCallBulkDeleteVM(data=bulk_data)
        serializer.is_valid(raise_exception=True)

        try:
            # Get existing relationships
            student_calls = StudentCall.objects.filter(
                call_id=call_id,
                student_id__in=student_ids
            )

            deleted_count = student_calls.count()
            student_calls.delete()

            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'Successfully removed {deleted_count} students from call'
            }

        except Exception as e:
            return {
                'success': False,
                'deleted_count': 0,
                'message': f'Failed to remove students from call: {str(e)}'
            }

    @staticmethod
    def get_call_capacity_info(call_id):
        """
        Get call capacity information

        Args:
            call_id: The call ID

        Returns:
            dict: Call capacity information
        """
        try:
            call = Call.objects.get(id=call_id)
            current_students = StudentCall.objects.filter(call_id=call_id).count()

            return {
                'call_id': call_id,
                'capacity': call.capacity,
                'current_students': current_students,
                'available_spots': call.capacity - current_students,
                'is_full': current_students >= call.capacity,
                'utilization_percentage': round((current_students / call.capacity) * 100, 2) if call.capacity > 0 else 0
            }

        except Call.DoesNotExist:
            return None

    @staticmethod
    def get_student_calls_statistics():
        """
        Get student call statistics

        Returns:
            dict: Student call statistics
        """
        total_relationships = StudentCall.objects.count()
        total_students_with_calls = StudentCall.objects.values('student_id').distinct().count()
        total_calls_with_students = StudentCall.objects.values('call_id').distinct().count()

        # Students without any calls
        total_students = Student.objects.filter(activity=True).count()
        students_without_calls = total_students - total_students_with_calls

        # Calls without any students
        total_calls = Call.objects.count()
        calls_without_students = total_calls - total_calls_with_students

        return {
            'total_student_call_relationships': total_relationships,
            'total_students_with_calls': total_students_with_calls,
            'total_calls_with_students': total_calls_with_students,
            'students_without_calls': students_without_calls,
            'calls_without_students': calls_without_students,
            'average_students_per_call': round(total_relationships / total_calls_with_students,
                                               2) if total_calls_with_students > 0 else 0,
            'average_calls_per_student': round(total_relationships / total_students_with_calls,
                                               2) if total_students_with_calls > 0 else 0
        }

    @staticmethod
    def check_student_call_exists(student_id, call_id):
        """
        Check if a student call relationship exists

        Args:
            student_id: The student ID
            call_id: The call ID

        Returns:
            bool: True if relationship exists, False otherwise
        """
        return StudentCall.objects.filter(student_id=student_id, call_id=call_id).exists()

    @staticmethod
    def _build_student_view_models_from_calls(student_calls):
        """
        Helper method to build student view models from student calls

        Args:
            student_calls: QuerySet of StudentCall objects

        Returns:
            List[dict]: List of student data in StudentVM format
        """
        student_view_models = []

        for student_call in student_calls:
            student = student_call.student
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
                'user_id': str(user.id)
            })

        return student_view_models

    @staticmethod
    def _build_student_call_view_models(student_calls):
        """
        Helper method to build student call view models

        Args:
            student_calls: QuerySet of StudentCall objects

        Returns:
            List[dict]: List of student call data
        """
        student_call_view_models = []

        for student_call in student_calls:
            student_call_view_models.append({
                'id': student_call.id,
                'student_id': student_call.student.id,
                'call_id': student_call.call.id,
                'student_name': student_call.student.user.name,
                'student_surname': student_call.student.user.surname,
                'call_capacity': student_call.call.capacity,
                'call_date_added': student_call.call.date_added
            })

        return student_call_view_models

    @staticmethod
    def _build_call_view_models_from_student_calls(student_calls):
        """
        Helper method to build call view models from student calls

        Args:
            student_calls: QuerySet of StudentCall objects

        Returns:
            List[dict]: List of call data
        """
        call_view_models = []

        for student_call in student_calls:
            call = student_call.call

            call_view_models.append({
                'id': call.id,
                'capacity': call.capacity,
                'date_added': call.date_added,
                'course_id': call.course_id,
                'course_name': call.course.name if hasattr(call, 'course') else None
            })

        return call_view_models

    @staticmethod
    def _check_call_capacity(call_id, required_spots=1):
        """
        Helper method to check call capacity

        Args:
            call_id: The call ID
            required_spots: Number of spots required (default 1)

        Returns:
            dict: Capacity check result with available_spots and is_available
        """
        try:
            call = Call.objects.get(id=call_id)
            current_students = StudentCall.objects.filter(call_id=call_id).count()
            available_spots = call.capacity - current_students
            
            return {
                'available_spots': available_spots,
                'is_available': available_spots >= required_spots,
                'capacity': call.capacity,
                'current_students': current_students
            }
        except Call.DoesNotExist:
            return {
                'available_spots': 0,
                'is_available': False,
                'capacity': 0,
                'current_students': 0
            }