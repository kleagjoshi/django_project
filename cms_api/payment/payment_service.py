from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from cms_api.models import Payment, GroupStudent, Group, CourseLecturer, Course, Student, ApplicationUser
from cms_api.enums import PaymentStatus
from .payment_vm import (
    PaymentVM, PaymentConfirmVM, StudentBlockVM, PaymentCreateVM,
    PaymentUpdateVM, PaymentRequestVM
)


class PaymentsService:

    @staticmethod
    def get_payments(group_student_id):
        """
        Get payments for a group student - creates them if they don't exist

        Args:
            group_student_id: The group student ID

        Returns:
            List[dict]: List of payment data in PaymentVM format
        """
        # Validate input
        request_data = {'group_student_id': group_student_id}
        serializer = PaymentRequestVM(data=request_data)
        serializer.is_valid(raise_exception=True)

        # Check if payments already exist for this group student
        existing_payments = Payment.objects.filter(group_student_id=group_student_id)

        if not existing_payments.exists():
            # No payments exist - create them based on course price and duration
            try:
                with transaction.atomic():
                    # Get the course information through the relationships
                    group_student = GroupStudent.objects.select_related(
                        'group__course_lecturer__course'
                    ).get(id=group_student_id)

                    group = group_student.group
                    course_lecturer = group.course_lecturer
                    course = course_lecturer.course

                    # Calculate monthly payment
                    monthly_payment = Decimal(course.price) / Decimal(course.duration)

                    payments_list = []

                    # Create payments for each month of the course
                    for month in range(1, course.duration + 1):
                        # Calculate due date (start date + month offset)
                        due_date = group.start_date + timedelta(days=(month - 1) * 30)  # Approximate monthly

                        payment = Payment.objects.create(
                            month=month,
                            amount=monthly_payment,
                            group_student_id=group_student_id,
                            status=PaymentStatus.UNPAID,
                            due_date=due_date
                        )

                        payments_list.append({
                            'id': payment.id,
                            'month': payment.month,
                            'amount': float(payment.amount),
                            'status': payment.status,
                            'due_date': payment.due_date.strftime('%Y-%m-%d') if payment.due_date else None,
                            'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else None
                        })

                    return payments_list

            except (GroupStudent.DoesNotExist, Group.DoesNotExist,
                    CourseLecturer.DoesNotExist, Course.DoesNotExist):
                return []
        else:
            # Payments already exist - return them
            existing_payments_list = []
            for payment in existing_payments:
                existing_payments_list.append({
                    'id': payment.id,
                    'month': payment.month,
                    'amount': float(payment.amount),
                    'status': payment.status,
                    'due_date': payment.due_date.strftime('%Y-%m-%d') if payment.due_date else None,
                    'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else None
                })

            return existing_payments_list

    @staticmethod
    def confirm_payment(payment_id):
        """
        Confirm a payment by setting status to Paid and payment_date to today

        Args:
            payment_id: The payment ID to confirm

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = PaymentStatusEnum.PAID
            payment.payment_date = timezone.now().date()
            payment.save()
            return True

        except Payment.DoesNotExist:
            return False

    @staticmethod
    def block_student(student_id):
        """
        Block a student by setting their user's is_enabled to False

        Args:
            student_id: The student ID to block

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            student = Student.objects.select_related('user').get(id=student_id)
            student.user.is_enabled = False
            student.user.save()
            return True

        except Student.DoesNotExist:
            return False

    @staticmethod
    def unblock_student(student_id):
        """
        Unblock a student by setting their user's is_enabled to True

        Args:
            student_id: The student ID to unblock

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            student = Student.objects.select_related('user').get(id=student_id)
            student.user.is_enabled = True
            student.user.save()
            return True

        except Student.DoesNotExist:
            return False

    @staticmethod
    def get_all_payments():
        """
        Get all payments in the system

        Returns:
            List[dict]: List of all payment data in PaymentVM format
        """
        payments = Payment.objects.all()
        return PaymentsService._build_payment_view_models(payments)

    @staticmethod
    def get_payment_by_id(payment_id):
        """
        Get a specific payment by ID

        Args:
            payment_id: The payment ID

        Returns:
            dict: Payment data in PaymentVM format or None if not found
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment_view_models = PaymentsService._build_payment_view_models([payment])
            return payment_view_models[0] if payment_view_models else None

        except Payment.DoesNotExist:
            return None

    @staticmethod
    def update_payment_by_id(payment_data, payment_id):
        """
        Update an existing payment

        Args:
            payment_data: Dict containing updated payment data
            payment_id: The payment ID to update

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = PaymentUpdateVM(data=payment_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            payment = Payment.objects.get(id=payment_id)
            payment.month = validated_data['month']
            payment.amount = validated_data['amount']
            payment.status = validated_data['status']
            payment.save()
            return True

        except Payment.DoesNotExist:
            return False

    @staticmethod
    def delete_payment_by_id(payment_id):
        """
        Delete a payment by ID

        Args:
            payment_id: The payment ID to delete

        Returns:
            bool: True if successful, False if payment not found
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.delete()
            return True

        except Payment.DoesNotExist:
            return False

    @staticmethod
    def get_payments_by_status(status):
        """
        Get payments by status (Paid/Pending)

        Args:
            status: PaymentStatusEnum value

        Returns:
            List[dict]: List of payment data in PaymentVM format
        """
        payments = Payment.objects.filter(status=status)
        return PaymentsService._build_payment_view_models(payments)

    @staticmethod
    def get_overdue_payments():
        """
        Get overdue payments (pending and overdue payments)

        Returns:
            List[dict]: List of overdue payment data
        """
        return PaymentsService.get_payments_by_status(PaymentStatus.UNPAID)

    @staticmethod
    def get_payments_statistics():
        """
        Get payment statistics

        Returns:
            dict: Payment statistics
        """
        all_payments = Payment.objects.all()

        if not all_payments.exists():
            return {
                'total_payments': 0,
                'paid_payments': 0,
                'pending_payments': 0,
                'total_amount': 0,
                'paid_amount': 0,
                'pending_amount': 0,
                'payment_completion_rate': 0
            }

        paid_payments = all_payments.filter(status=PaymentStatus.PAID)
        pending_payments = all_payments.filter(status=PaymentStatus.UNPAID)

        total_amount = sum(float(p.amount) for p in all_payments)
        paid_amount = sum(float(p.amount) for p in paid_payments)
        pending_amount = sum(float(p.amount) for p in pending_payments)

        completion_rate = (paid_payments.count() / all_payments.count()) * 100 if all_payments.count() > 0 else 0

        return {
            'total_payments': all_payments.count(),
            'paid_payments': paid_payments.count(),
            'pending_payments': pending_payments.count(),
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'payment_completion_rate': round(completion_rate, 2)
        }

    @staticmethod
    def _build_payment_view_models(payments):
        """
        Helper method to build payment view models from queryset

        Args:
            payments: QuerySet of Payment objects

        Returns:
            List[dict]: List of payment data in PaymentVM format
        """
        payment_view_models = []

        for payment in payments:
            payment_view_models.append({
                'id': payment.id,
                'month': payment.month,
                'amount': float(payment.amount),
                'status': payment.status,
                'due_date': payment.due_date.strftime('%Y-%m-%d') if payment.due_date else None,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else None
            })

        return payment_view_models