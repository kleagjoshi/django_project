from rest_framework import serializers
from cms_api.models import Payment, GroupStudent
from cms_api.enums import PaymentStatus


class PaymentVM(serializers.Serializer):
    """Payment ViewModel"""
    id = serializers.IntegerField()
    month = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    due_date = serializers.DateField(allow_null=True, required=False)
    payment_date = serializers.DateField(allow_null=True, required=False)


class PaymentConfirmVM(serializers.Serializer):
    """Payment Confirmation ViewModel"""
    payment_id = serializers.IntegerField()

    def validate_payment_id(self, value):
        """Validate that the payment exists"""
        if not Payment.objects.filter(id=value).exists():
            raise serializers.ValidationError("Payment does not exist")
        return value


class StudentBlockVM(serializers.Serializer):
    """Student Block/Unblock ViewModel"""
    student_id = serializers.IntegerField()


class PaymentCreateVM(serializers.Serializer):
    """Payment Creation ViewModel (for manual creation if needed)"""
    month = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    group_student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    due_date = serializers.DateField(allow_null=True, required=False)

    def validate_group_student_id(self, value):
        """Validate that the group student exists"""
        if not GroupStudent.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group student does not exist")
        return value


class PaymentUpdateVM(serializers.Serializer):
    """Payment Update ViewModel"""
    month = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    status = serializers.ChoiceField(choices=PaymentStatus.choices)


class PaymentRequestVM(serializers.Serializer):
    """Payment Request ViewModel for GetPayments"""
    group_student_id = serializers.IntegerField()

    def validate_group_student_id(self, value):
        """Validate that the group student exists"""
        if not GroupStudent.objects.filter(id=value).exists():
            raise serializers.ValidationError("Group student does not exist")
        return value