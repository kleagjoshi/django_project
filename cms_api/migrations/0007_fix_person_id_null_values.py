# Generated by Django 4.2.7 on 2025-06-05 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms_api', '0006_payment_due_date_payment_payment_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationuser',
            name='person_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
