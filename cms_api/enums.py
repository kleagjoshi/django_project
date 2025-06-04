from django.db import models

class GroupStatus(models.IntegerChoices):
    ONGOING  = 0, 'Ongoing'
    FINISHED = 1, 'Finished'

class PaymentStatus(models.IntegerChoices):
    UNPAID = 0, 'Unpaid'
    PAID = 1, 'Paid'

class StudentGroupStatus(models.IntegerChoices):
    UNSATISFIED = 0, 'Unsatisfied'
    SATISFIED = 1, 'Satisfied'

class GenderChoices(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'