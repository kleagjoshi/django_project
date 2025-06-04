from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Student, Lecturer
from cms_api.permissions import IsLecturerOrAdmin, IsOwnerStudentOrAdmin, CanViewOwnData
from .student_service import StudentService
from .student_vm import (
    StudentCreateVM, StudentEditVM, StudentVM, StudentSimpleVM,
    StudentSearchVM, StudentStatusUpdateVM, StudentReturnVM
)
from cms_api.serializers import StudentSerializer
from cms_api.enums import StudentGroupStatus


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'destroy', 'return_student']:
            # Only lecturers and admin can create/delete students
            permission_classes = [IsLecturerOrAdmin]
        elif self.action in ['update', 'partial_update']:
            # Students can update their own data, lecturers/admin can update anyone
            permission_classes = [IsOwnerStudentOrAdmin]
        elif self.action in ['list', 'simple', 'passive', 'search', 'by_employment', 'all', 'statistics']:
            # Lecturers and admin can view student lists
            permission_classes = [IsLecturerOrAdmin]
        elif self.action in ['retrieve']:
            # Students can view their own data, others need lecturer/admin permissions
            permission_classes = [CanViewOwnData]
        elif self.action in ['update_status']:
            # Only lecturers and admin can update student status in groups
            permission_classes = [IsLecturerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        if self.request.user.is_staff:
            # Admin can see all students
            return Student.objects.all()
        
        try:
            # Lecturer can see students in their groups
            lecturer = Lecturer.objects.get(user=self.request.user)
            return Student.objects.filter(
                group_students__group__course_lecturer__lecturer=lecturer
            ).distinct()
        except Lecturer.DoesNotExist:
            pass
        
        try:
            # Students can see only themselves
            student = Student.objects.get(user=self.request.user)
            return Student.objects.filter(id=student.id)
        except Student.DoesNotExist:
            pass
        
        # Default: empty queryset if user has no role
        return Student.objects.none()

    @extend_schema(
        request=StudentCreateVM,
        responses={201: StudentVM},
        description="Create a new student"
    )
    def create(self, request):
        try:
            student_data = StudentService.create_student(request.data)
            return Response(student_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get all active students with full details"
    )
    def list(self, request):
        students = StudentService.get_all_student_details()
        return Response(students)

    @extend_schema(
        responses={200: StudentVM},
        description="Get student by ID"
    )
    def retrieve(self, request, pk=None):
        student_data = StudentService.get_student_by_id(pk)
        if student_data:
            return Response(student_data)
        else:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=StudentEditVM,
        responses={200: StudentVM},
        description="Edit student"
    )
    def update(self, request, pk=None):
        try:
            student_data = StudentService.edit_student(pk, request.data)
            if student_data:
                return Response(student_data)
            else:
                return Response(
                    {'error': 'Student not found or update failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Soft delete a student"
    )
    def destroy(self, request, pk=None):
        success = StudentService.delete_student(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: StudentSimpleVM(many=True)},
        description="Get simple students for dropdowns"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        try:
            students = StudentService.get_simple_students()
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get all passive (inactive) students"
    )
    @action(detail=False, methods=['get'])
    def passive(self, request):
        try:
            students = StudentService.get_all_passive_students()
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Search students by name and surname",
        parameters=[
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Student name (optional)'
            ),
            OpenApiParameter(
                name='surname',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Student surname (optional)'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search students by name and surname
        """
        name = request.query_params.get('name', '')
        surname = request.query_params.get('surname', '')

        try:
            students = StudentService.search_student(name, surname)
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentReturnVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Reactivate a soft-deleted student"
    )
    @action(detail=False, methods=['post'])
    def return_student(self, request):
        try:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response(
                    {'error': 'student_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = StudentService.return_student(student_id)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found or already active'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentStatusUpdateVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update student status in group"
    )
    @action(detail=False, methods=['post'])
    def update_status(self, request):
        try:
            student_id = request.data.get('student_id')
            new_status = request.data.get('new_status')

            if not student_id or not new_status:
                return Response(
                    {'error': 'student_id and new_status are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = StudentService.update_student_status(student_id, new_status)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found or not assigned to any group'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get students by employment status",
        parameters=[
            OpenApiParameter(
                name='employed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Employment status (true/false)'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_employment(self, request):
        """
        Get students by employment status - additional functionality
        """
        employed_param = request.query_params.get('employed')
        if employed_param is None:
            return Response(
                {'error': 'employed parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employed = employed_param.lower() == 'true'
            students = StudentService.get_students_by_employment_status(employed)
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: StudentVM(many=True)},
        description="Get all students (both active and inactive)"
    )
    @action(detail=False, methods=['get'])
    def all(self, request):
        """
        Get all students - additional functionality
        """
        try:
            students = StudentService.get_all_students()
            return Response(students)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_students': {'type': 'integer'},
            'active_students': {'type': 'integer'},
            'inactive_students': {'type': 'integer'},
            'employed_students': {'type': 'integer'},
            'unemployed_students': {'type': 'integer'},
            'students_with_groups': {'type': 'integer'},
            'students_without_groups': {'type': 'integer'}
        }}},
        description="Get student statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get student statistics - additional functionality
        """
        try:
            stats = StudentService.get_students_statistics()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )