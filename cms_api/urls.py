from django.urls import path, include
from rest_framework.routers import DefaultRouter

from cms_api.call.call_views import CallViewSet
from cms_api.course.course_views import CourseViewSet
from cms_api.group.group_views import GroupViewSet
from cms_api.group_student.group_student_views import GroupStudentViewSet
from cms_api.lecturer.lecturer_views import LecturerViewSet
from cms_api.material.material_views import MaterialViewSet
from cms_api.payment.payment_views import PaymentViewSet
from cms_api.student.student_views import StudentViewSet
from cms_api.student_call.student_call_views import StudentCallViewSet
from cms_api.views import (
    RegisterView, LoginView, LogoutView, UserProfileView, CustomTokenRefreshView
)

router = DefaultRouter()
# router.register(r'users', views.ApplicationUserViewSet)
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'lecturers', LecturerViewSet, basename='lecturers')
router.register(r'students', StudentViewSet, basename='students')
# router.register(r'course-lecturers', views.CourseLecturerViewSet)
router.register(r'calls', CallViewSet, basename='calls')
router.register(r'student-calls', StudentCallViewSet, basename='student-calls')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'group-students', GroupStudentViewSet, basename='group-students')
router.register(r'materials', MaterialViewSet, basename='materials')
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('api/', include(router.urls)),
    # Authentication endpoints
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/refresh/', CustomTokenRefreshView.as_view(), name='auth_refresh'),
    path('api/auth/profile/', UserProfileView.as_view(), name='auth_profile'),
]