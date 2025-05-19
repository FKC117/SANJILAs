from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import timedelta, datetime
from accounts.models import DailySales, MonthlyReport, ProductAnalytics, AdminActivity
from order.models import Order
from shop.models import Product
from decimal import Decimal
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Populates dashboard data from existing orders and products'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting dashboard data population...')
        
        # Get all orders
        orders = Order.objects.all()
        
        # Process daily sales
        self.populate_daily_sales(orders)
        
        # Process monthly reports
        self.populate_monthly_reports(orders)
        
        # Process product analytics
        self.populate_product_analytics(orders)
        
        # Create initial admin activity
        self.create_initial_activity()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated dashboard data!'))

    def populate_daily_sales(self, orders):
        self.stdout.write('Processing daily sales...')
        
        # Group orders by date
        daily_orders = {}
        for order in orders:
            date = order.order_date.date()
            if date not in daily_orders:
                daily_orders[date] = []
            daily_orders[date].append(order)
        
        # Create or update DailySales records
        for date, day_orders in daily_orders.items():
            total_sales = sum(order.total_amount for order in day_orders)
            total_cost = sum(
                sum(item.product.buying_price * item.quantity for item in order.items.all())
                for order in day_orders
            )
            total_expenses = sum(order.shipping_cost for order in day_orders)
            
            DailySales.objects.update_or_create(
                date=date,
                defaults={
                    'total_sales': total_sales,
                    'total_orders': len(day_orders),
                    'total_cost': total_cost,
                    'total_expenses': total_expenses,
                    'total_advertisement': Decimal('0'),  # Set based on your data
                    'total_salary': Decimal('0'),  # Set based on your data
                }
            )

    def populate_monthly_reports(self, orders):
        self.stdout.write('Processing monthly reports...')
        
        # Group orders by month
        monthly_orders = {}
        for order in orders:
            month_key = (order.order_date.year, order.order_date.month)
            if month_key not in monthly_orders:
                monthly_orders[month_key] = []
            monthly_orders[month_key].append(order)
        
        # Create or update MonthlyReport records
        for (year, month), month_orders in monthly_orders.items():
            total_sales = sum(order.total_amount for order in month_orders)
            total_cost = sum(
                sum(item.product.buying_price * item.quantity for item in order.items.all())
                for order in month_orders
            )
            total_expenses = sum(order.shipping_cost for order in month_orders)
            
            MonthlyReport.objects.update_or_create(
                year=year,
                month=month,
                defaults={
                    'total_sales': total_sales,
                    'total_orders': len(month_orders),
                    'total_cost': total_cost,
                    'total_expenses': total_expenses,
                    'total_advertisement': Decimal('0'),  # Set based on your data
                    'total_salary': Decimal('0'),  # Set based on your data
                }
            )

    def populate_product_analytics(self, orders):
        self.stdout.write('Processing product analytics...')
        
        # Get all products
        products = Product.objects.all()
        
        # Process each product
        for product in products:
            # Get all order items for this product
            product_items = []
            for order in orders:
                for item in order.items.filter(product=product):
                    product_items.append(item)
            
            if product_items:
                total_quantity = sum(item.quantity for item in product_items)
                total_sales = sum(item.unit_price * item.quantity for item in product_items)
                total_cost = sum(item.product.buying_price * item.quantity for item in product_items)
                
                # Create analytics for today
                ProductAnalytics.objects.update_or_create(
                    product=product,
                    date=timezone.now().date(),
                    defaults={
                        'quantity_sold': total_quantity,
                        'total_sales': total_sales,
                        'total_cost': total_cost,
                        'stock_level': product.stock,
                    }
                )

    def create_initial_activity(self):
        self.stdout.write('Creating initial admin activity...')
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
        if not admin_user:
            self.stdout.write('No superuser or staff user found. Skipping AdminActivity creation.')
            return
        AdminActivity.objects.create(
            admin=admin_user,
            activity_type='system_config',
            description='Dashboard data populated from existing orders and products',
            ip_address='127.0.0.1'
        ) 