from cms_api.models import Student, Lecturer


class UserRoleMiddleware:
    """
    Middleware to add user role information to the request object.
    This makes it easier to access user roles in views and permissions.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add user role information to the request
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user_role = self.get_user_role(request.user)
            request.is_admin = request.user.is_staff
            request.is_lecturer = self.is_lecturer(request.user)
            request.is_student = self.is_student(request.user)
        else:
            request.user_role = 'anonymous'
            request.is_admin = False
            request.is_lecturer = False
            request.is_student = False

        response = self.get_response(request)
        return response

    def get_user_role(self, user):
        """
        Determine the user's role
        """
        if user.is_staff:
            return 'admin'
        
        if self.is_lecturer(user):
            return 'lecturer'
        
        if self.is_student(user):
            return 'student'
        
        return 'user'  # Authenticated user without specific role

    def is_lecturer(self, user):
        """
        Check if user is a lecturer
        """
        try:
            Lecturer.objects.get(user=user)
            return True
        except Lecturer.DoesNotExist:
            return False

    def is_student(self, user):
        """
        Check if user is a student
        """
        try:
            Student.objects.get(user=user)
            return True
        except Student.DoesNotExist:
            return False 