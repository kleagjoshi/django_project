from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Group, Lecturer, Student
from cms_api.permissions import IsLecturerOrAdmin, CanViewOwnData, IsOwnerLecturerOrAdmin
from .group_service import GroupsService
from .group_vm import (
    GroupCreateVM, GroupEditVM, GroupGetVM, GroupSimpleVM,
    CourseLecturerGroupVM
)
from cms_api.serializers import GroupSerializer
from cms_api.enums import GroupStatus


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Only lecturers and admin can create groups
            permission_classes = [IsLecturerOrAdmin]
        elif self.action in ['update', 'partial_update', 'destroy', 'update_status']:
            # Only the lecturer who owns the group or admin can modify
            permission_classes = [IsOwnerLecturerOrAdmin]
        elif self.action in ['list', 'retrieve', 'simple', 'by_status', 'course_lecturers', 'statistics']:
            # Everyone can view general lists and statistics
            permission_classes = [IsAuthenticated]
        elif self.action in ['by_lecturer', 'by_student']:
            # Users can view their own data
            permission_classes = [CanViewOwnData]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        if self.request.user.is_staff:
            # Admin can see all groups
            return Group.objects.all()
        
        try:
            # Lecturer can see their own groups
            lecturer = Lecturer.objects.get(user=self.request.user)
            return Group.objects.filter(course_lecturer__lecturer=lecturer)
        except Lecturer.DoesNotExist:
            pass
        
        try:
            # Students can see groups they're enrolled in
            student = Student.objects.get(user=self.request.user)
            return Group.objects.filter(group_students__student=student).distinct()
        except Student.DoesNotExist:
            pass
        
        # Default: empty queryset if user has no role
        return Group.objects.none()

    @extend_schema(
        request=GroupCreateVM,
        responses={201: GroupGetVM},
        description="Create a new group with students. Specify start_date and duration; end_date will be automatically calculated."
    )
    def create(self, request):
        """
        Add a new group
        """
        try:
            group = GroupsService.add_group(request.data)
            group_data = GroupsService.get_group_by_id(group.id)
            return Response(group_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: GroupGetVM(many=True)},
        description="Get all groups with course lecturer and student details"
    )
    def list(self, request):
        """
        Get all groups
        """
        groups = GroupsService.get_all_groups()
        return Response(groups)

    @extend_schema(
        responses={200: GroupGetVM},
        description="Get a specific group by ID with full details"
    )
    def retrieve(self, request, pk=None):
        """
        Get group by ID
        """
        try:
            group_data = GroupsService.get_group_by_id(pk)
            return Response(group_data)
        except Exception as e:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=GroupEditVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update group classroom and capacity"
    )
    def update(self, request, pk=None):
        """
        Update group
        """
        success = GroupsService.update_group_by_id(pk, request.data)
        if success:
            group_data = GroupsService.get_group_by_id(pk)
            return Response(group_data)
        else:
            return Response(
                {'error': 'Group not found or update failed'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: GroupSimpleVM(many=True)},
        description="Get simple list of groups (ID, classroom, course, lecturer, status)"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Get simple groups - additional functionality
        """
        groups = GroupsService.get_simple_groups()
        return Response(groups)

    @extend_schema(
        responses={200: GroupGetVM(many=True)},
        description="Get groups filtered by status",
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Group status (WAITING, ACTIVE, COMPLETED)',
                enum=[choice[0] for choice in GroupStatus.choices]
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """
        Get groups by status
        """
        status_param = request.query_params.get('status')
        if not status_param:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate status
            valid_statuses = [choice[0] for choice in GroupStatus.choices]
            if status_param not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Must be one of: {valid_statuses}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            groups = GroupsService.get_all_groups_by_status(status_param)
            return Response(groups)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: GroupGetVM(many=True)},
        description="Get all groups for a specific lecturer",
        parameters=[
            OpenApiParameter(
                name='lecturer_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the lecturer'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_lecturer(self, request):
        """
        Get groups by lecturer
        """
        lecturer_id = request.query_params.get('lecturer_id')
        if not lecturer_id:
            return Response(
                {'error': 'lecturer_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            groups = GroupsService.get_all_groups_by_lecturer_id(lecturer_id)
            return Response(groups)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: GroupGetVM(many=True)},
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
    def by_student(self, request):
        """
        Get groups by student
        """
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            groups = GroupsService.get_all_groups_by_student_id(student_id)
            return Response(groups)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update group status to ACTIVE"
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update status
        """
        success = GroupsService.update_status(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: CourseLecturerGroupVM(many=True)},
        description="Get all course lecturers"
    )
    @action(detail=False, methods=['get'])
    def course_lecturers(self, request):
        """
        Get course lecturers
        """
        course_lecturers = GroupsService.get_all_course_lecturers()
        return Response(course_lecturers)

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_groups': {'type': 'integer'},
            'groups_by_status': {'type': 'object'},
            'total_students': {'type': 'integer'}
        }}},
        description="Get group statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get group statistics - additional functionality
        """
        all_groups = GroupsService.get_all_groups()

        if not all_groups:
            return Response({
                'total_groups': 0,
                'groups_by_status': {},
                'total_students': 0
            })

        total_groups = len(all_groups)

        # Count groups by status
        groups_by_status = {}
        total_students = 0

        for group in all_groups:
            status_key = group['status']
            groups_by_status[status_key] = groups_by_status.get(status_key, 0) + 1
            total_students += len(group['students'])

        return Response({
            'total_groups': total_groups,
            'groups_by_status': groups_by_status,
            'total_students': total_students
        })