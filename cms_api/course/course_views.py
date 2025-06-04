from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Course
from cms_api.permissions import IsAdminOrReadOnly, IsLecturerOrAdmin
from cms_api.course.course_service import CourseService
from cms_api.course.course_vm import (
    CourseCreateVM, CourseEditVM, CourseVM, CourseSimpleVM
)
from cms_api.serializers import CourseSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]  # Read access for all, write access only for admin

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve', 'simple', 'by_lecturer']:
            # Everyone can view courses
            permission_classes = [IsAuthenticated]
        elif self.action in ['passive', 'return_course']:
            # Only lecturers and admin can view passive courses and return them
            permission_classes = [IsLecturerOrAdmin]
        else:
            # Create, update, delete - admin only
            permission_classes = [IsAdminOrReadOnly]
        
        return [permission() for permission in permission_classes]

    @extend_schema(
        request=CourseCreateVM,
        responses={201: CourseVM},
        description="Create a new course with lecturer assignments"
    )
    def create(self, request):
        """
        Add a new course
        """
        try:
            course = CourseService.add_course(request.data)
            course_data = CourseService.get_course_by_id(course.id)
            return Response(course_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: CourseVM(many=True)},
        description="Get all active courses with full details"
    )
    def list(self, request):
        """
        Get all courses
        """
        courses = CourseService.get_all_courses()
        return Response(courses)

    @extend_schema(
        responses={200: CourseVM},
        description="Get a specific course by ID with full details"
    )
    def retrieve(self, request, pk=None):
        """
        Get course by ID
        """
        try:
            course_data = CourseService.get_course_by_id(pk)
            return Response(course_data)
        except Exception as e:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=CourseEditVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update an existing course"
    )
    def update(self, request, pk=None):
        """
        Update course
        """
        success = CourseService.update_course_by_id(pk, request.data)
        if success:
            course_data = CourseService.get_course_by_id(pk)
            return Response(course_data)
        else:
            return Response(
                {'error': 'Course not found or update failed'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Soft delete a course (set inactive)"
    )
    def destroy(self, request, pk=None):
        """
        Soft delete course 
        """
        success = CourseService.delete_course_by_id(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Course not found or has ongoing groups'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: CourseSimpleVM(many=True)},
        description="Get simple list of active courses (ID and name only)"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Get simple courses
        """
        courses = CourseService.get_all_simple_courses()
        return Response(courses)

    @extend_schema(
        responses={200: CourseVM(many=True)},
        description="Get all inactive/deleted courses"
    )
    @action(detail=False, methods=['get'])
    def passive(self, request):
        """
        Get passive courses
        """
        courses = CourseService.get_passive_courses()
        return Response(courses)

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Reactivate a soft-deleted course"
    )
    @action(detail=True, methods=['post'])
    def return_course(self, request, pk=None):
        """
        Return (reactivate) course
        """
        success = CourseService.return_course(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Course not found or already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: CourseVM(many=True)},
        description="Get courses assigned to a specific lecturer",
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
        Get courses by lecturer - additional functionality
        """
        lecturer_id = request.query_params.get('lecturer_id')
        if not lecturer_id:
            return Response(
                {'error': 'lecturer_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        courses = Course.objects.filter(
            course_lecturers__lecturer_id=lecturer_id,
            active=True
        ).prefetch_related(
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

            course_view_models.append({
                'id': course.id,
                'name': course.name,
                'duration': course.duration,
                'price': course.price,
                'level': course.level,
                'calls': call_base_vms,
                'lectures': course_lecturer_vms
            })

        return Response(course_view_models)