from rest_framework.permissions import BasePermission
from cms_api.models import Student, Lecturer


class IsAdminOrReadOnly(BasePermission):
    """
    Permission that allows read access to authenticated users,
    but write access only to admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read permissions for authenticated users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only for admin users
        return request.user.is_staff


class IsAdminOnly(BasePermission):
    """
    Permission that allows access only to admin users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


class IsLecturerOrAdmin(BasePermission):
    """
    Permission that allows access to lecturers and admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if user is a lecturer
        try:
            Lecturer.objects.get(user=request.user)
            return True
        except Lecturer.DoesNotExist:
            return False


class IsStudentOrAdmin(BasePermission):
    """
    Permission that allows access to students and admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if user is a student
        try:
            Student.objects.get(user=request.user)
            return True
        except Student.DoesNotExist:
            return False


class IsOwnerLecturerOrAdmin(BasePermission):
    """
    Permission that allows access to the lecturer who owns the resource, or admin users.
    Used for group-specific operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if user is a lecturer
        try:
            Lecturer.objects.get(user=request.user)
            return True
        except Lecturer.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if the lecturer owns this group
        try:
            lecturer = Lecturer.objects.get(user=request.user)
            # For Group objects
            if hasattr(obj, 'course_lecturer'):
                return obj.course_lecturer.lecturer == lecturer
            # For other related objects, customize as needed
            return False
        except Lecturer.DoesNotExist:
            return False


class IsOwnerStudentOrAdmin(BasePermission):
    """
    Permission that allows access to the student who owns the resource, or admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if user is a student
        try:
            Student.objects.get(user=request.user)
            return True
        except Student.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Check if the student owns this resource
        try:
            student = Student.objects.get(user=request.user)
            # For Student objects
            if hasattr(obj, 'user') and obj.user == request.user:
                return True
            # For GroupStudent objects
            if hasattr(obj, 'student'):
                return obj.student == student
            # For Payment objects (through group_student)
            if hasattr(obj, 'group_student'):
                return obj.group_student.student == student
            return False
        except Student.DoesNotExist:
            return False


class CanManagePayments(BasePermission):
    """
    Permission for payment management - lecturers can view/confirm payments for their groups,
    admin can do everything.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Lecturers can manage payments
        try:
            Lecturer.objects.get(user=request.user)
            return True
        except Lecturer.DoesNotExist:
            pass
        
        # Students can only view their own payments (read-only)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            try:
                Student.objects.get(user=request.user)
                return True
            except Student.DoesNotExist:
                pass
        
        return False


class CanViewOwnData(BasePermission):
    """
    Permission that allows users to view their own data and related information.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # All authenticated users can access (object-level permissions will restrict)
        return True

    def has_object_permission(self, request, view, obj):
        # Admin users always have access
        if request.user.is_staff:
            return True
        
        # Users can access their own data
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Lecturers can access their groups and related data
        try:
            lecturer = Lecturer.objects.get(user=request.user)
            if hasattr(obj, 'course_lecturer'):
                return obj.course_lecturer.lecturer == lecturer
        except Lecturer.DoesNotExist:
            pass
        
        # Students can access their group data
        try:
            student = Student.objects.get(user=request.user)
            if hasattr(obj, 'student'):
                return obj.student == student
            if hasattr(obj, 'group_student') and obj.group_student.student == student:
                return True
        except Student.DoesNotExist:
            pass
        
        return False 