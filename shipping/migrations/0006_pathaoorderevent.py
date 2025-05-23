# Generated by Django 5.1.4 on 2025-05-20 12:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0005_pathaocredentials_webhook_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='PathaoOrderEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('order.created', 'Order Created'), ('order.updated', 'Order Updated'), ('pickup.requested', 'Pickup Requested'), ('pickup.assigned', 'Assigned For Pickup'), ('pickup.completed', 'Pickup Completed'), ('pickup.failed', 'Pickup Failed'), ('pickup.cancelled', 'Pickup Cancelled'), ('sorting.hub', 'At the Sorting Hub'), ('in.transit', 'In Transit'), ('last.mile.hub', 'Received at Last Mile Hub'), ('delivery.assigned', 'Assigned for Delivery'), ('delivery.completed', 'Delivered'), ('delivery.partial', 'Partial Delivery'), ('return.requested', 'Return'), ('delivery.failed', 'Delivery Failed'), ('order.on_hold', 'On Hold'), ('payment.invoice', 'Payment Invoice'), ('return.paid', 'Paid Return'), ('exchange.requested', 'Exchange')], max_length=50)),
                ('event_data', models.JSONField(help_text='Raw event data from webhook')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pathao_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='shipping.pathaoorder')),
            ],
            options={
                'verbose_name_plural': 'Pathao Order Events',
                'ordering': ['-created_at'],
            },
        ),
    ]
