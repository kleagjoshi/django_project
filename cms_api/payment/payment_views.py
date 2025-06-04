from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Payment, Lecturer, Student
from cms_api.permissions import CanManagePayments, IsOwnerStudentOrAdmin, IsLecturerOrAdmin
from .payment_service import PaymentsService
from .payment_vm import (
    PaymentVM, PaymentConfirmVM, StudentBlockVM, PaymentCreateVM,
    PaymentUpdateVM, PaymentRequestVM
)
from cms_api.serializers import PaymentSerializer
from cms_api.enums import PaymentStatus


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [CanManagePayments]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['get_payments']:
            # Students can view their own payments, lecturers can view their group payments
            permission_classes = [IsOwnerStudentOrAdmin]
        elif self.action in ['confirm_payment', 'block_student', 'unblock_student']:
            # Only lecturers and admin can manage payments and students
            permission_classes = [IsLecturerOrAdmin]
        elif self.action in ['list', 'retrieve', 'by_status', 'overdue', 'statistics']:
            # Lecturers and admin can view payment reports
            permission_classes = [IsLecturerOrAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only admin can modify payment records directly
            permission_classes = [IsLecturerOrAdmin]
        else:
            permission_classes = [CanManagePayments]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        if self.request.user.is_staff:
            # Admin can see all payments
            return Payment.objects.all()
        
        try:
            # Lecturer can see payments for their groups
            lecturer = Lecturer.objects.get(user=self.request.user)
            return Payment.objects.filter(
                group_student__group__course_lecturer__lecturer=lecturer
            )
        except Lecturer.DoesNotExist:
            pass
        
        try:
            # Students can see their own payments
            student = Student.objects.get(user=self.request.user)
            return Payment.objects.filter(group_student__student=student)
        except Student.DoesNotExist:
            pass
        
        # Default: empty queryset if user has no role
        return Payment.objects.none()

    @extend_schema(
        responses={200: PaymentVM(many=True)},
        description="Get all payments in the system"
    )
    def list(self, request):
        """
        Get all payments - additional functionality
        """
        payments = PaymentsService.get_all_payments()
        return Response(payments)

    @extend_schema(
        responses={200: PaymentVM},
        description="Get a specific payment by ID"
    )
    def retrieve(self, request, pk=None):
        """
        Get payment by ID
        """
        payment_data = PaymentsService.get_payment_by_id(pk)
        if payment_data:
            return Response(payment_data)
        else:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=PaymentUpdateVM,
        responses={200: PaymentVM},
        description="Update payment information"
    )
    def update(self, request, pk=None):
        """
        Update payment
        """
        try:
            success = PaymentsService.update_payment_by_id(request.data, pk)
            if success:
                payment_data = PaymentsService.get_payment_by_id(pk)
                return Response(payment_data)
            else:
                return Response(
                    {'error': 'Payment not found or update failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Delete a payment"
    )
    def destroy(self, request, pk=None):
        """
        Delete payment
        """
        success = PaymentsService.delete_payment_by_id(pk)
        if success:
            return Response({'success': True})
        else:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={200: PaymentVM(many=True)},
        description="Get payments for a group student - creates them if they don't exist",
        parameters=[
            OpenApiParameter(
                name='group_student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group student'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def get_payments(self, request):
        """
        Get payments for group student
        This is the main "Check Payments" button functionality
        """
        group_student_id = request.query_params.get('group_student_id')
        if not group_student_id:
            return Response(
                {'error': 'group_student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payments = PaymentsService.get_payments(int(group_student_id))
            return Response(payments)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=PaymentConfirmVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Confirm a payment"
    )
    @action(detail=False, methods=['post'])
    def confirm_payment(self, request):
        """
        Confirm payment
        """
        try:
            payment_id = request.data.get('payment_id')
            if not payment_id:
                return Response(
                    {'error': 'payment_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = PaymentsService.confirm_payment(payment_id)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Payment not found or confirmation failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentBlockVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Block a student"
    )
    @action(detail=False, methods=['post'])
    def block_student(self, request):
        """
        Block student
        """
        try:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response(
                    {'error': 'student_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = PaymentsService.block_student(student_id)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found or blocking failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=StudentBlockVM,
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Unblock a student"
    )
    @action(detail=False, methods=['post'])
    def unblock_student(self, request):
        try:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response(
                    {'error': 'student_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success = PaymentsService.unblock_student(student_id)
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Student not found or unblocking failed'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: PaymentVM(many=True)},
        description="Get payments by status",
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Payment status (Paid/Unpaid)',
                enum=[PaymentStatus.PAID, PaymentStatus.UNPAID]
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """
        Get payments by status - additional functionality
        """
        status_param = request.query_params.get('status')
        if not status_param:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate status
        if status_param not in [PaymentStatus.PAID, PaymentStatus.UNPAID]:
            return Response(
                {'error': 'Invalid status. Use "PAID" or "PENDING"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payments = PaymentsService.get_payments_by_status(status_param)
            return Response(payments)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: PaymentVM(many=True)},
        description="Get overdue (pending) payments"
    )
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get overdue payments - additional functionality
        """
        try:
            payments = PaymentsService.get_overdue_payments()
            return Response(payments)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_payments': {'type': 'integer'},
            'paid_payments': {'type': 'integer'},
            'pending_payments': {'type': 'integer'},
            'total_amount': {'type': 'number'},
            'paid_amount': {'type': 'number'},
            'pending_amount': {'type': 'number'},
            'payment_completion_rate': {'type': 'number'}
        }}},
        description="Get payment statistics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get payment statistics - additional functionality
        """
        try:
            stats = PaymentsService.get_payments_statistics()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )