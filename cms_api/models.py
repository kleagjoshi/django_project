from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from cms_api.enums import GroupStatus,PaymentStatus,StudentGroupStatus
from course_management_system import settings


class ApplicationUser(AbstractUser):
    person_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    surname = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    birth_place = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    is_enabled = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.name} {self.surname})"


class Lecturer(models.Model):
    contract_start = models.DateTimeField()
    contract_end = models.DateTimeField()
    university_degree = models.CharField(max_length=20)
    activity = models.BooleanField()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lecturer_profile')

class Course(models.Model):
    name = models.CharField(max_length=20)
    duration = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    price = models.IntegerField(validators=[MinValueValidator(0)])
    level = models.CharField(max_length=20)
    active = models.BooleanField()


class CourseLecturer(models.Model):
    """Many-to-many relationship between Course and Lecturer"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_lecturers')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='course_lecturers')
    assigned_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.course.name} - {self.lecturer.user.name} {self.lecturer.user.surname}"

    class Meta:
        unique_together = ['course', 'lecturer']

class Student(models.Model):
    employed = models.BooleanField()
    activity = models.BooleanField()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')

class Group(models.Model):
    classroom = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=GroupStatus.choices)
    course_lecturer = models.ForeignKey(CourseLecturer, on_delete=models.CASCADE, related_name='groups')

    @property
    def course_name(self):
        return self.course_lecturer.course.name

    @property
    def duration(self):
        return self.course_lecturer.course.duration

    @property
    def level(self):
        return self.course_lecturer.course.level

    @property
    def price(self):
        return self.course_lecturer.course.price


class GroupStudent(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_students')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='group_students')
    status = models.CharField(max_length=20, choices=StudentGroupStatus.choices, default=StudentGroupStatus.UNSATISFIED)
    feedback = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="Feedback rating from 1 to 10"
    )
    class Meta:
        unique_together = ['group', 'student']

class Call(models.Model):
    capacity = models.IntegerField(validators=[MinValueValidator(0)])
    date_added = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='calls') # call-course 1-M

    def clean(self):
        """Validate that application_deadline is after date_added"""
        from django.core.exceptions import ValidationError
        super().clean()
        
        if self.application_deadline and self.date_added:
            if self.application_deadline <= self.date_added:
                raise ValidationError({
                    'application_deadline': 'Application deadline must be after the date added.'
                })

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation"""
        self.full_clean()
        super().save(*args, **kwargs)

class StudentCall(models.Model):
    """Many-to-many relationship between Student and Call"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_calls')
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='student_calls')
    applied_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.name} {self.student.user.surname} - {self.call.course.name}"

    class Meta:
        unique_together = ['student', 'call']

class Material(models.Model):
    topic = models.CharField(max_length=25)
    description = models.TextField()
    week = models.IntegerField()
    link = models.URLField()

    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name='materials') #material-group 1-M

class Payment(models.Model):
    month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.IntegerField(choices=PaymentStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    group_student = models.ForeignKey(GroupStudent,on_delete=models.CASCADE,related_name='payments')

    class Meta:
        unique_together = ['group_student', 'month']
