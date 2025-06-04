from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Call
from .call_service import CallsService
from .call_vm import CallCreateVM, CallEditVM, CallVM, CallSimpleVM
from cms_api.serializers import CallSerializer


class CallViewSet(viewsets.ModelViewSet):
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CallCreateVM,
        responses={201: CallVM},
        description="Create a new call for a course"
    )
    def create(self, request):
        """Add a new call"""
        try:
            call = CallsService.add_call(request.data)
            call_data = CallsService.get_call_by_id(call.id)
            return Response(call_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: CallVM(many=True)},
        description="Get all calls with course details"
    )
    def list(self, request):
        """Get all calls"""
        calls = CallsService.get_all_calls()
        return Response(calls)

    @extend_schema(
        responses={200: CallVM},
        description="Get a specific call by ID with course details"
    )
    def retrieve(self, request, pk=None):
        """Get call by ID"""
        try:
            call_data = CallsService.get_call_by_id(pk)
            return Response(call_data)
        except Exception as e:
            return Response(
                {'error': 'Call not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=CallEditVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Update call capacity"
    )
    def update(self, request, pk=None):
        """Update call"""
        success = CallsService.update_call_by_id(pk, request.data)
        if success:
            call_data = CallsService.get_call_by_id(pk)
            return Response(call_data)
        else:
            return Response(
                {'error': 'Call not found or update failed'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Delete a call and its related student calls"
    )
    def destroy(self, request, pk=None):
        """Delete call by id"""
        success = CallsService.delete_call_by_id(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Call not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: CallSimpleVM(many=True)},
        description="Get simple list of calls (ID, capacity, course name)"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Get simple calls - additional functionality
        """
        calls = CallsService.get_simple_calls()
        return Response(calls)

    @extend_schema(
        responses={200: CallVM(many=True)},
        description="Get all calls for a specific course",
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
        Get calls by course - additional functionality
        """
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'course_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            calls = CallsService.get_calls_by_course(course_id)
            return Response(calls)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_calls': {'type': 'integer'},
            'total_capacity': {'type': 'integer'},
            'average_capacity': {'type': 'number'}
        }}},
        description="Get call statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get call statistics - additional functionality
        """
        calls = CallsService.get_all_calls()

        if not calls:
            return Response({
                'total_calls': 0,
                'total_capacity': 0,
                'average_capacity': 0
            })

        total_calls = len(calls)
        total_capacity = sum(call['capacity'] for call in calls)
        average_capacity = total_capacity / total_calls

        return Response({
            'total_calls': total_calls,
            'total_capacity': total_capacity,
            'average_capacity': round(average_capacity, 2)
        })