from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from cms_api.models import Call, Course, StudentCall
from .call_vm import CallCreateVM, CallVM, CallEditVM, CallSimpleVM


class CallsService:

    @staticmethod
    def add_call(call_data):
        """
        Add a new call

        Args:
            call_data: Dict containing call data including course_id

        Returns:
            Call: The created call instance
        """
        # Validate input data
        serializer = CallCreateVM(data=call_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        with transaction.atomic():
            # Get the course
            course = get_object_or_404(Course, id=validated_data['course_id'])

            # Create the call
            call = Call.objects.create(
                capacity=validated_data['capacity'],
                date_added=timezone.now(),
                application_deadline=validated_data['application_deadline'],
                course=course
            )

        return call

    @staticmethod
    def get_all_calls():
        """
        Get all calls with their course information

        Returns:
            List[dict]: List of call data in CallVM format
        """
        calls = Call.objects.select_related('course').all()

        call_view_models = []
        for call in calls:
            call_view_models.append({
                'id': call.id,
                'capacity': call.capacity,
                'date_added': call.date_added,
                'course_id': call.course.id,
                'course_name': call.course.name,
                'course_duration': call.course.duration,
                'course_level': call.course.level,
                'course_price': call.course.price
            })

        return call_view_models

    @staticmethod
    def get_call_by_id(call_id):
        """
        Get a specific call by ID with course details

        Args:
            call_id: The call ID

        Returns:
            dict: Call data in CallVM format

        Raises:
            Call.DoesNotExist: If call not found
        """
        call = get_object_or_404(
            Call.objects.select_related('course'),
            id=call_id
        )

        call_view_model = {
            'id': call.id,
            'capacity': call.capacity,
            'date_added': call.date_added,
            'course_id': call.course.id,
            'course_name': call.course.name,
            'course_duration': call.course.duration,
            'course_level': call.course.level,
            'course_price': call.course.price
        }

        return call_view_model

    @staticmethod
    def update_call_by_id(call_id, call_data):
        """
        Update an existing call

        Args:
            call_id: The call ID to update
            call_data: Dict containing updated call data

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = CallEditVM(data=call_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            call = Call.objects.get(id=call_id)
            call.capacity = validated_data['capacity']
            call.save()
            return True

        except Call.DoesNotExist:
            return False

    @staticmethod
    def delete_call_by_id(call_id):
        """
        Delete a call and its related StudentCalls

        Args:
            call_id: The call ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                call = Call.objects.prefetch_related('student_calls').get(id=call_id)

                # Delete related StudentCalls first
                StudentCall.objects.filter(call=call).delete()

                # Delete the call
                call.delete()

            return True

        except Call.DoesNotExist:
            return False

    @staticmethod
    def get_calls_by_course(course_id):
        """
        Get all calls for a specific course

        Args:
            course_id: The course ID

        Returns:
            List[dict]: List of call data for the course
        """
        calls = Call.objects.filter(course_id=course_id).select_related('course')

        call_view_models = []
        for call in calls:
            call_view_models.append({
                'id': call.id,
                'capacity': call.capacity,
                'date_added': call.date_added,
                'course_id': call.course.id,
                'course_name': call.course.name,
                'course_duration': call.course.duration,
                'course_level': call.course.level,
                'course_price': call.course.price
            })

        return call_view_models

    @staticmethod
    def get_simple_calls():
        """
        Get all calls in simple format

        Returns:
            List[dict]: List of simple call data
        """
        calls = Call.objects.select_related('course').all()

        call_view_models = []
        for call in calls:
            call_view_models.append({
                'id': call.id,
                'capacity': call.capacity,
                'course_name': call.course.name
            })

        return call_view_models