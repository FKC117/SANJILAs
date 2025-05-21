from django.core.management.base import BaseCommand
from order.models import Order
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates test orders with different payment methods for testing COD charges'

    def handle(self, *args, **options):
        # Create a test order with payment_method='cash'
        order_cash, created = Order.objects.get_or_create(
            customer_name='Test Customer Cash',
            customer_phone='1234567890',
            customer_email='test@example.com',
            shipping_address='Test Address, Test City, Test Country',
            city='1',
            city_name='Dhaka',
            zone='1',
            area='1',
            shipping_location='inside_dhaka',
            shipping_cost=Decimal('75.00'),
            total_amount=Decimal('575.00'),  # 500 + 75 shipping
            order_date=timezone.now(),
            status='delivered',
            payment_method='cash',  # This is the COD payment method
            defaults={
                'payment_status': 'paid',
                'order_notes': 'Test order with cash payment method'
            }
        )
        
        # Create a test order with payment_method='bkash'
        order_bkash, created = Order.objects.get_or_create(
            customer_name='Test Customer bKash',
            customer_phone='9876543210',
            customer_email='test2@example.com',
            shipping_address='Test Address 2, Test City, Test Country',
            city='1',
            city_name='Dhaka',
            zone='1',
            area='1',
            shipping_location='inside_dhaka',
            shipping_cost=Decimal('75.00'),
            total_amount=Decimal('675.00'),  # 600 + 75 shipping
            order_date=timezone.now(),
            status='delivered',
            payment_method='bkash',  # Mobile banking payment
            defaults={
                'payment_status': 'paid',
                'order_notes': 'Test order with bKash payment method'
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created test orders'))
        
        # Print created orders
        self.stdout.write(f"Cash order: {order_cash} - payment_method: {order_cash.payment_method}")
        self.stdout.write(f"bKash order: {order_bkash} - payment_method: {order_bkash.payment_method}")
        
        # Print all order payment methods
        Order.print_payment_methods() 