# Generated by Django 5.1.4 on 2025-05-22 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_stockmovement_created_by_alter_stockmovement_product_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='invoice_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_file',
            field=models.FileField(blank=True, null=True, upload_to='invoices/'),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_generated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
