# Generated by Django 4.2.22 on 2025-06-04 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms_api', '0005_groupstudent_feedback_alter_group_end_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
