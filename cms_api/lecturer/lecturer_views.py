from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Lecturer
from .lecturer_service import LecturersService
from .lecturer_vm import (
    LecturerCreateVM, LecturerEditVM, LecturerVM, LecturerSimpleVM,
    LecturerSearchVM
)
from cms_api.serializers import LecturerSerializer


class LecturerViewSet(viewsets.ModelViewSet):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LecturerCreateVM,
        responses={201: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Create a new lecturer with course relationships"
    )
    def create(self, request):
        """
        Add a new lecturer
        """
        try:
            success = LecturersService.add_lecturer(request.data)
            if success:
                return Response({'success': True}, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Lecturer already exists for this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: LecturerVM(many=True)},
        description="Get all active lecturers with user and course details"
    )
    def list(self, request):
        """
        Get all lecturers
        """
        lecturers = LecturersService.get_all_lecturers()
        return Response(lecturers)

    @extend_schema(
        responses={200: LecturerVM},
        description="Get a specific lecturer by ID with full details"
    )
    def retrieve(self, request, pk=None):
        """
        Get lecturer by ID
        """
        lecturer_data = LecturersService.get_lecturer_by_id(pk)
        if lecturer_data:
            return Response(lecturer_data)
        else:
            return Response(
                {'error': 'Lecturer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=LecturerEditVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update lecturer information and course relationships"
    )
    def update(self, request, pk=None):
        """
        Update lecturer
        """
        try:
            success = LecturersService.update_lecturer_by_id(pk, request.data)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Lecturer not found or update failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Soft delete a lecturer (check for ongoing groups)"
    )
    def destroy(self, request, pk=None):
        """
        Delete lecturer
        """
        success = LecturersService.delete_lecturer_by_id(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Lecturer not found or has ongoing groups'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: LecturerSimpleVM(many=True)},
        description="Get simple list of lecturers (for forms)"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Get simple lecturers
        """
        lecturers = LecturersService.get_all_simple_lecturers()
        return Response(lecturers)

    @extend_schema(
        responses={200: LecturerVM(many=True)},
        description="Get all inactive lecturers"
    )
    @action(detail=False, methods=['get'])
    def passive(self, request):
        """
        Get passive lecturers
        """
        lecturers = LecturersService.get_all_passive_lecturers()
        return Response(lecturers)

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Reactivate a soft-deleted lecturer"
    )
    @action(detail=True, methods=['post'])
    def return_lecturer(self, request, pk=None):
        """
        Return lecturer
        """
        success = LecturersService.return_lecturer(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Lecturer not found or already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: LecturerVM(many=True)},
        description="Search lecturers by name and/or surname",
        parameters=[
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Name to search for',
                required=False
            ),
            OpenApiParameter(
                name='surname',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Surname to search for',
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search lecturers
        """
        name = request.query_params.get('name', '')
        surname = request.query_params.get('surname', '')

        if not name and not surname:
            return Response(
                {'error': 'At least one search parameter (name or surname) is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lecturers = LecturersService.search_lecturer(
                name=name if name else None,
                surname=surname if surname else None
            )
            return Response(lecturers)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_lecturers': {'type': 'integer'},
            'active_lecturers': {'type': 'integer'},
            'passive_lecturers': {'type': 'integer'},
            'lecturers_with_courses': {'type': 'integer'},
            'average_courses_per_lecturer': {'type': 'number'}
        }}},
        description="Get lecturer statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get lecturer statistics - additional functionality
        """
        try:
            active_lecturers = LecturersService.get_all_lecturers()
            passive_lecturers = LecturersService.get_all_passive_lecturers()

            total_lecturers = len(active_lecturers) + len(passive_lecturers)
            lecturers_with_courses = sum(1 for lecturer in active_lecturers if lecturer['courses'])

            total_courses = sum(len(lecturer['courses']) for lecturer in active_lecturers)
            average_courses = total_courses / len(active_lecturers) if active_lecturers else 0

            return Response({
                'total_lecturers': total_lecturers,
                'active_lecturers': len(active_lecturers),
                'passive_lecturers': len(passive_lecturers),
                'lecturers_with_courses': lecturers_with_courses,
                'average_courses_per_lecturer': round(average_courses, 2)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: LecturerVM(many=True)},
        description="Get lecturers by course ID",
        parameters=[
            OpenApiParameter(
                name='course_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the course'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """
        Get lecturers by course - additional functionality
        """
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'course_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            all_lecturers = LecturersService.get_all_lecturers()
            filtered_lecturers = []

            for lecturer in all_lecturers:
                lecturer_courses = [course['course_id'] for course in lecturer['courses']]
                if int(course_id) in lecturer_courses:
                    filtered_lecturers.append(lecturer)

            return Response(filtered_lecturers)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )