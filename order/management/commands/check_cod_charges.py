from django.core.management.base import BaseCommand
from order.models import Order
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal
import json

class Command(BaseCommand):
    help = 'Calculates and displays COD charges from orders'

    def handle(self, *args, **options):
        # Count orders by payment method
        payment_methods = Order.objects.values_list('payment_method', flat=True).distinct()
        self.stdout.write(f"All payment methods in database: {list(payment_methods)}")
        
        for method in payment_methods:
            count = Order.objects.filter(payment_method=method).count()
            self.stdout.write(f"Payment method '{method}': {count} orders")
        
        # Calculate COD charges for cash payment method
        cash_orders = Order.objects.filter(payment_method='cash')
        cash_order_count = cash_orders.count()
        self.stdout.write(f"Found {cash_order_count} cash orders")
        
        if cash_order_count > 0:
            # Get total amount for cash orders
            cash_total = cash_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            cash_shipping = cash_orders.aggregate(total=Sum('shipping_cost'))['total'] or 0
            cash_product = cash_total - cash_shipping
            
            # Calculate COD charges (0.5% of product price)
            cod_charges = cash_product * Decimal('0.005')
            
            self.stdout.write(f"Cash order total amount: {cash_total}")
            self.stdout.write(f"Cash order shipping cost: {cash_shipping}")
            self.stdout.write(f"Cash order product price: {cash_product}")
            self.stdout.write(f"COD charges (0.5% of product price): {cod_charges}")
            
            # Show individual cash orders
            self.stdout.write("\nIndividual cash orders:")
            for order in cash_orders:
                product_price = order.total_amount - order.shipping_cost
                cod_charge = product_price * Decimal('0.005')
                self.stdout.write(f"Order #{order.id}: Total={order.total_amount}, Shipping={order.shipping_cost}, Product={product_price}, COD={cod_charge}")
        else:
            self.stdout.write("No cash orders found.")
            
        # Calculate using queryset and aggregation
        cod_charges_query = Order.objects.filter(payment_method='cash').aggregate(
            total=Sum(F('total_amount') - F('shipping_cost')) * Decimal('0.005')
        )['total'] or Decimal('0')
        
        self.stdout.write(f"\nCOD charges using query aggregation: {cod_charges_query}")
        
        # Try other payment methods too
        for method in payment_methods:
            if method != 'cash':
                cod_charges_alt = Order.objects.filter(payment_method=method).aggregate(
                    total=Sum(F('total_amount') - F('shipping_cost')) * Decimal('0.005')
                )['total'] or Decimal('0')
                
                self.stdout.write(f"COD charges for '{method}' orders: {cod_charges_alt}")
                
        # Return a success message
        self.stdout.write(self.style.SUCCESS('Successfully calculated COD charges')) 