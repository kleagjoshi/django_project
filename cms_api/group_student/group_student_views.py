from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import GroupStudent
from .group_student_service import GroupStudentsService
from .group_student_vm import (
    GroupStudentCreateVM, GroupStudentRemoveVM, GroupStudentFeedbackVM,
    GroupStudentsRequestVM, GroupStudentStatusUpdateVM, GroupStudentBulkCreateVM,
    GroupStudentBulkRemoveVM, GroupStudentVM
)
from ..student.student_vm import StudentVM
from cms_api.serializers import GroupStudentSerializer


class GroupStudentViewSet(viewsets.ModelViewSet):
    queryset = GroupStudent.objects.all()
    serializer_class = GroupStudentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get all students by group ID",
        parameters=[
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def students_by_group(self, request):
        """
        Get all students by group ID
        """
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response(
                {'error': 'group_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            students = GroupStudentsService.get_all_students_by_group_id(int(group_id))
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=GroupStudentCreateVM,
        responses={201: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Add student to group"
    )
    def create(self, request):
        """
        Add student to group
        """
        try:
            student_id = request.data.get('student_id')
            group_id = request.data.get('group_id')
            
            if not student_id or not group_id:
                return Response(
                    {'error': 'student_id and group_id are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = GroupStudentsService.add_student_to_group(student_id, group_id)
            if success:
                return Response({'success': True}, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to add student to group'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: GroupStudentVM(many=True)},
        description="Get all group student relationships"
    )
    def list(self, request):
        """
        Get all group student relationships
        """
        group_students = GroupStudentsService.get_all_group_students()
        return Response(group_students)

    @extend_schema(
        request=GroupStudentRemoveVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Remove student from group"
    )
    @action(detail=False, methods=['post'])
    def remove_student(self, request):
        """
        Remove student from group
        """
        try:
            student_id = request.data.get('student_id')
            group_id = request.data.get('group_id')
            
            if not student_id or not group_id:
                return Response(
                    {'error': 'student_id and group_id are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = GroupStudentsService.remove_student_from_group(student_id, group_id)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found in group or removal failed'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=GroupStudentFeedbackVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update feedback for student in group"
    )
    @action(detail=False, methods=['post'])
    def update_feedback(self, request):
        """
        Update feedback for student in group
        """
        try:
            student_id = request.data.get('student_id')
            group_id = request.data.get('group_id')
            feedback = request.data.get('feedback')
            
            if student_id is None or group_id is None or feedback is None:
                return Response(
                    {'error': 'student_id, group_id, and feedback are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = GroupStudentsService.update_feedback(student_id, group_id, feedback)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found in group'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'array', 'items': {'type': 'object'}}},
        description="Get all groups for a specific student",
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
    def groups_by_student(self, request):
        """
        Get all groups for a specific student - additional functionality
        """
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            groups = GroupStudentsService.get_groups_by_student_id(int(student_id))
            return Response(groups)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=GroupStudentStatusUpdateVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update student status in group"
    )
    @action(detail=False, methods=['post'])
    def update_status(self, request):
        """
        Update student status in group - enhanced functionality
        """
        try:
            student_id = request.data.get('student_id')
            group_id = request.data.get('group_id')
            status_value = request.data.get('status')
            
            if not student_id or not group_id or not status_value:
                return Response(
                    {'error': 'student_id, group_id, and status are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = GroupStudentsService.update_student_status(student_id, group_id, status_value)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found in group'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=GroupStudentBulkCreateVM,
        responses={200: {'type': 'object', 'properties': {
            'success': {'type': 'boolean'},
            'created_count': {'type': 'integer'},
            'message': {'type': 'string'}
        }}},
        description="Add multiple students to a group - bulk operation"
    )
    @action(detail=False, methods=['post'])
    def bulk_add_students(self, request):
        """
        Add multiple students to a group - enhanced functionality
        """
        try:
            group_id = request.data.get('group_id')
            student_ids = request.data.get('student_ids', [])
            
            if not group_id or not student_ids:
                return Response(
                    {'error': 'group_id and student_ids are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = GroupStudentsService.add_bulk_students_to_group(group_id, student_ids)
            
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
        request=GroupStudentBulkRemoveVM,
        responses={200: {'type': 'object', 'properties': {
            'success': {'type': 'boolean'},
            'deleted_count': {'type': 'integer'},
            'message': {'type': 'string'}
        }}},
        description="Remove multiple students from a group - bulk operation"
    )
    @action(detail=False, methods=['post'])
    def bulk_remove_students(self, request):
        """
        Remove multiple students from a group - enhanced functionality
        """
        try:
            group_id = request.data.get('group_id')
            student_ids = request.data.get('student_ids', [])
            
            if not group_id or not student_ids:
                return Response(
                    {'error': 'group_id and student_ids are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = GroupStudentsService.remove_bulk_students_from_group(group_id, student_ids)
            
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
            'group_id': {'type': 'integer'},
            'capacity': {'type': 'integer'},
            'current_students': {'type': 'integer'},
            'available_spots': {'type': 'integer'},
            'is_full': {'type': 'boolean'},
            'utilization_percentage': {'type': 'number'}
        }}},
        description="Get group capacity information",
        parameters=[
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def group_capacity(self, request):
        """
        Get group capacity information - enhanced functionality
        """
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response(
                {'error': 'group_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            capacity_info = GroupStudentsService.get_group_capacity_info(int(group_id))
            if capacity_info:
                return Response(capacity_info)
            else:
                return Response(
                    {'error': 'Group not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_group_student_relationships': {'type': 'integer'},
            'total_students_with_groups': {'type': 'integer'},
            'total_groups_with_students': {'type': 'integer'},
            'students_without_groups': {'type': 'integer'},
            'groups_without_students': {'type': 'integer'},
            'average_students_per_group': {'type': 'number'},
            'average_groups_per_student': {'type': 'number'}
        }}},
        description="Get group student statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get group student statistics - enhanced functionality
        """
        try:
            stats = GroupStudentsService.get_group_students_statistics()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'exists': {'type': 'boolean'}}}},
        description="Check if a group student relationship exists",
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the student'
            ),
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def check_exists(self, request):
        """
        Check if a group student relationship exists - enhanced functionality
        """
        student_id = request.query_params.get('student_id')
        group_id = request.query_params.get('group_id')
        
        if not student_id or not group_id:
            return Response(
                {'error': 'student_id and group_id parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exists = GroupStudentsService.check_group_student_exists(int(student_id), int(group_id))
            return Response({'exists': exists})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'feedback': {'type': 'integer'}}}},
        description="Get student feedback in a specific group",
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the student'
            ),
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def get_feedback(self, request):
        """
        Get student feedback in a specific group - enhanced functionality
        """
        student_id = request.query_params.get('student_id')
        group_id = request.query_params.get('group_id')
        
        if not student_id or not group_id:
            return Response(
                {'error': 'student_id and group_id parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            feedback = GroupStudentsService.get_student_feedback_in_group(int(student_id), int(group_id))
            if feedback is not None:
                return Response({'feedback': feedback})
            else:
                return Response(
                    {'error': 'Student not found in group'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 