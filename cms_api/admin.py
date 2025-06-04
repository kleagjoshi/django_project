from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    ApplicationUser, Lecturer, Course, CourseLecturer, Student, 
    Group, GroupStudent, Call, StudentCall, Material, Payment
)


class ApplicationUserAdmin(UserAdmin):
    list_display = ('username', 'person_id', 'name', 'surname', 'email', 'is_enabled', 'is_staff', 'created_date')
    list_filter = ('is_enabled', 'is_staff', 'is_superuser', 'gender', 'created_date')
    search_fields = ('username', 'person_id', 'name', 'surname', 'email')
    ordering = ('-created_date',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Information', {
            'fields': ('person_id', 'name', 'surname', 'father_name', 'birthday', 'birth_place', 'gender')
        }),
        ('Status', {
            'fields': ('is_enabled', 'created_date')
        }),
    )
    readonly_fields = ('created_date',)


class CourseLecturerInline(admin.TabularInline):
    model = CourseLecturer
    extra = 1


class LecturerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'university_degree', 'activity', 'contract_start', 'contract_end')
    list_filter = ('activity', 'university_degree', 'contract_start', 'contract_end')
    search_fields = ('user__name', 'user__surname', 'user__username', 'university_degree')
    date_hierarchy = 'contract_start'
    inlines = [CourseLecturerInline]
    
    def get_full_name(self, obj):
        return f"{obj.user.name} {obj.user.surname}"
    get_full_name.short_description = 'Full Name'


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'level', 'active')
    list_filter = ('active', 'level')
    search_fields = ('name', 'level')
    inlines = [CourseLecturerInline]


class CourseLecturerAdmin(admin.ModelAdmin):
    list_display = ('course', 'get_lecturer_name', 'assigned_date')
    list_filter = ('assigned_date', 'course', 'lecturer__activity')
    search_fields = ('course__name', 'lecturer__user__name', 'lecturer__user__surname')
    date_hierarchy = 'assigned_date'
    
    def get_lecturer_name(self, obj):
        return f"{obj.lecturer.user.name} {obj.lecturer.user.surname}"
    get_lecturer_name.short_description = 'Lecturer'


class GroupStudentInline(admin.TabularInline):
    model = GroupStudent
    extra = 1


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1


class StudentCallInline(admin.TabularInline):
    model = StudentCall
    extra = 1


class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employed', 'activity', 'get_username')
    list_filter = ('employed', 'activity')
    search_fields = ('user__name', 'user__surname', 'user__username')
    inlines = [GroupStudentInline, StudentCallInline]
    
    def get_full_name(self, obj):
        return f"{obj.user.name} {obj.user.surname}"
    get_full_name.short_description = 'Full Name'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'classroom', 'start_date', 'end_date', 'status', 'get_lecturer', 'get_duration')
    list_filter = ('status', 'start_date', 'end_date', 'course_lecturer__course__level')
    search_fields = ('classroom', 'course_lecturer__course__name', 'course_lecturer__lecturer__user__name')
    date_hierarchy = 'start_date'
    inlines = [GroupStudentInline, MaterialInline]
    readonly_fields = ('end_date', 'get_duration', 'get_calculated_duration')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course_lecturer', 'classroom', 'status')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date'),
            'description': 'End date is automatically calculated based on start date and course duration.'
        }),
        ('Duration Information', {
            'fields': ('get_duration', 'get_calculated_duration'),
            'classes': ('collapse',)
        }),
    )
    
    def get_lecturer(self, obj):
        return f"{obj.course_lecturer.lecturer.user.name} {obj.course_lecturer.lecturer.user.surname}"
    get_lecturer.short_description = 'Lecturer'
    
    def get_duration(self, obj):
        return f"{obj.course_lecturer.course.duration} days"
    get_duration.short_description = 'Course Duration'
    
    def get_calculated_duration(self, obj):
        if obj.calculated_duration_days is not None:
            return f"{obj.calculated_duration_days} days"
        return "Not calculated"
    get_calculated_duration.short_description = 'Calculated Duration'


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ('created_at',)


class GroupStudentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_group_course', 'get_group_classroom', 'feedback', 'status')
    list_filter = ('status', 'group__status', 'group__start_date')
    search_fields = ('student__user__name', 'student__user__surname', 'group__course_lecturer__course__name')
    inlines = [PaymentInline]
    
    def get_student_name(self, obj):
        return f"{obj.student.user.name} {obj.student.user.surname}"
    get_student_name.short_description = 'Student'
    
    def get_group_course(self, obj):
        return obj.group.course_name
    get_group_course.short_description = 'Course'
    
    def get_group_classroom(self, obj):
        return obj.group.classroom
    get_group_classroom.short_description = 'Classroom'


class CallAdmin(admin.ModelAdmin):
    list_display = ('get_course_name', 'capacity', 'date_added', 'application_deadline')
    list_filter = ('date_added', 'application_deadline', 'course')
    search_fields = ('course__name',)
    date_hierarchy = 'date_added'
    inlines = [StudentCallInline]
    
    def get_course_name(self, obj):
        return obj.course.name
    get_course_name.short_description = 'Course'


class StudentCallAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_course_name', 'applied_date')
    list_filter = ('applied_date', 'call__course')
    search_fields = ('student__user__name', 'student__user__surname', 'call__course__name')
    date_hierarchy = 'applied_date'
    
    def get_student_name(self, obj):
        return f"{obj.student.user.name} {obj.student.user.surname}"
    get_student_name.short_description = 'Student'
    
    def get_course_name(self, obj):
        return obj.call.course.name
    get_course_name.short_description = 'Course'


class MaterialAdmin(admin.ModelAdmin):
    list_display = ('topic', 'week', 'get_group_course', 'get_group_classroom', 'link')
    list_filter = ('week', 'group__course_lecturer__course', 'group__status')
    search_fields = ('topic', 'description', 'group__course_lecturer__course__name')
    
    def get_group_course(self, obj):
        return obj.group.course_name
    get_group_course.short_description = 'Course'
    
    def get_group_classroom(self, obj):
        return obj.group.classroom
    get_group_classroom.short_description = 'Classroom'


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_group_course', 'month', 'amount', 'status', 'created_at')
    list_filter = ('status', 'month', 'created_at', 'group_student__group__course_lecturer__course')
    search_fields = ('group_student__student__user__name', 'group_student__student__user__surname', 'group_student__group__course_lecturer__course__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def get_student_name(self, obj):
        return f"{obj.group_student.student.user.name} {obj.group_student.student.user.surname}"
    get_student_name.short_description = 'Student'
    
    def get_group_course(self, obj):
        return obj.group_student.group.course_name
    get_group_course.short_description = 'Course'


# Register all models with their admin classes
admin.site.register(ApplicationUser, ApplicationUserAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseLecturer, CourseLecturerAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupStudent, GroupStudentAdmin)
admin.site.register(Call, CallAdmin)
admin.site.register(StudentCall, StudentCallAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Payment, PaymentAdmin)
