# Generated by Django 5.1.4 on 2025-05-20 05:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_order_area_name_order_city_name_order_zone_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='shipping_address',
            field=models.TextField(help_text='Enter the shipping address minimum 10 characters', validators=[django.core.validators.MinLengthValidator(10)]),
        ),
    ]
