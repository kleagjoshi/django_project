from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import StudentCall
from .student_call_service import StudentCallsService
from .student_call_vm import (
    StudentCallCreateVM, StudentCallDeleteVM, StudentCallVM,
    CallStudentsRequestVM, StudentCallBulkCreateVM, StudentCallBulkDeleteVM
)
from cms_api.serializers import StudentCallSerializer
from ..student.student_vm import StudentVM


class StudentCallViewSet(viewsets.ModelViewSet):
    queryset = StudentCall.objects.all()
    serializer_class = StudentCallSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StudentCallCreateVM,
        responses={201: {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'message': {'type': 'string'}}}},
        description="Add a student call connection"
    )
    def create(self, request):
        """
        Add student call connection - equivalent to C# AddStudentCall method
        """
        try:
            student_id = request.data.get('student_id')
            call_id = request.data.get('call_id')

            if not student_id or not call_id:
                return Response(
                    {'error': 'student_id and call_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = StudentCallsService.add_student_call(student_id, call_id)
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result['message']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentCallVM(many=True)},
        description="Get all student call relationships"
    )
    def list(self, request):
        """
        Get all student call relationships
        """
        student_calls = StudentCallsService.get_all_student_calls()
        return Response(student_calls)

    @extend_schema(
        request=StudentCallDeleteVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'message': {'type': 'string'}}}},
        description="Delete a student call connection - equivalent to C# DeleteStudentCall method"
    )
    @action(detail=False, methods=['post'])
    def delete_connection(self, request):
        """
        Delete student call connection - equivalent to C# DeleteStudentCall method
        """
        try:
            student_id = request.data.get('student_id')
            call_id = request.data.get('call_id')

            if not student_id or not call_id:
                return Response(
                    {'error': 'student_id and call_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = StudentCallsService.delete_student_call(student_id, call_id)
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result['message']},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get all students by call ID - equivalent to C# GetAllStdsByCallId method",
        parameters=[
            OpenApiParameter(
                name='call_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the call'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def students_by_call(self, request):
        """
        Get all students by call ID - equivalent to C# GetAllStdsByCallId method
        """
        call_id = request.query_params.get('call_id')
        if not call_id:
            return Response(
                {'error': 'call_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            students = StudentCallsService.get_all_students_by_call_id(int(call_id))
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'array', 'items': {'type': 'object'}}},
        description="Get all calls for a specific student",
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the student'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def calls_by_student(self, request):
        """
        Get all calls for a specific student - additional functionality
        """
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            calls = StudentCallsService.get_student_calls_by_student_id(int(student_id))
            return Response(calls)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentCallBulkCreateVM,
        responses={200: {'type': 'object', 'properties': {
            'success': {'type': 'boolean'},
            'created_count': {'type': 'integer'},
            'message': {'type': 'string'}
        }}},
        description="Add multiple students to a call - bulk operation with capacity validation"
    )
    @action(detail=False, methods=['post'])
    def bulk_add_students(self, request):
        """
        Add multiple students to a call - enhanced functionality with capacity checking
        """
        try:
            call_id = request.data.get('call_id')
            student_ids = request.data.get('student_ids', [])

            if not call_id or not student_ids:
                return Response(
                    {'error': 'call_id and student_ids are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = StudentCallsService.add_bulk_student_calls(call_id, student_ids)

            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result['message'], 'created_count': result.get('created_count', 0)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentCallBulkDeleteVM,
        responses={200: {'type': 'object', 'properties': {
            'success': {'type': 'boolean'},
            'deleted_count': {'type': 'integer'},
            'message': {'type': 'string'}
        }}},
        description="Remove multiple students from a call - bulk operation"
    )
    @action(detail=False, methods=['post'])
    def bulk_remove_students(self, request):
        """
        Remove multiple students from a call - enhanced functionality
        """
        try:
            call_id = request.data.get('call_id')
            student_ids = request.data.get('student_ids', [])

            if not call_id or not student_ids:
                return Response(
                    {'error': 'call_id and student_ids are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = StudentCallsService.delete_bulk_student_calls(call_id, student_ids)

            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'call_id': {'type': 'integer'},
            'capacity': {'type': 'integer'},
            'current_students': {'type': 'integer'},
            'available_spots': {'type': 'integer'},
            'is_full': {'type': 'boolean'},
            'utilization_percentage': {'type': 'number'}
        }}},
        description="Get call capacity information",
        parameters=[
            OpenApiParameter(
                name='call_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the call'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def call_capacity(self, request):
        """
        Get call capacity information - enhanced functionality
        """
        call_id = request.query_params.get('call_id')
        if not call_id:
            return Response(
                {'error': 'call_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            capacity_info = StudentCallsService.get_call_capacity_info(int(call_id))
            if capacity_info:
                return Response(capacity_info)
            else:
                return Response(
                    {'error': 'Call not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_student_call_relationships': {'type': 'integer'},
            'total_students_with_calls': {'type': 'integer'},
            'total_calls_with_students': {'type': 'integer'},
            'students_without_calls': {'type': 'integer'},
            'calls_without_students': {'type': 'integer'},
            'average_students_per_call': {'type': 'number'},
            'average_calls_per_student': {'type': 'number'}
        }}},
        description="Get student call statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get student call statistics - enhanced functionality
        """
        try:
            stats = StudentCallsService.get_student_calls_statistics()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'exists': {'type': 'boolean'}}}},
        description="Check if a student call relationship exists",
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the student'
            ),
            OpenApiParameter(
                name='call_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the call'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def check_exists(self, request):
        """
        Check if a student call relationship exists - enhanced functionality
        """
        student_id = request.query_params.get('student_id')
        call_id = request.query_params.get('call_id')

        if not student_id or not call_id:
            return Response(
                {'error': 'student_id and call_id parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exists = StudentCallsService.check_student_call_exists(int(student_id), int(call_id))
            return Response({'exists': exists})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )