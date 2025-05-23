from django.shortcuts import render

# Create your views here.
# finance/views.py

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .services import FinancialCalculationService
from .models import Order
from decimal import Decimal

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def dashboard(request):
    """Main financial dashboard"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = timezone.datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = timezone.datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass

    # Get all financial summaries
    sales_summary = FinancialCalculationService.get_sales_summary(start_date, end_date)
    product_summary = FinancialCalculationService.get_product_sales_summary(start_date, end_date)
    payment_summary = FinancialCalculationService.get_payment_summary(start_date, end_date)
    profit_summary = FinancialCalculationService.get_profit_summary(start_date, end_date)
    daily_summary = FinancialCalculationService.get_daily_sales_summary(start_date, end_date)

    context = {
        'sales_summary': sales_summary,
        'product_summary': product_summary,
        'payment_summary': payment_summary,
        'profit_summary': profit_summary,
        'daily_summary': daily_summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finance/dashboard.html', context)

@user_passes_test(is_superuser)
def sales_report(request):
    """Detailed sales report"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = timezone.datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = timezone.datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass

    # Get sales summary
    sales_summary = FinancialCalculationService.get_sales_summary(start_date, end_date)
    daily_summary = FinancialCalculationService.get_daily_sales_summary(start_date, end_date)
    
    # Calculate additional metrics
    total_sales = sales_summary['total_sales']
    total_orders = sales_summary['total_orders']
    total_items = sum(data.get('count', 0) for data in sales_summary['status_breakdown'].values())
    average_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Calculate growth rate (comparing with previous period)
    previous_start = start_date - (end_date - start_date)
    previous_summary = FinancialCalculationService.get_sales_summary(previous_start, start_date)
    previous_sales = previous_summary['total_sales']
    growth_rate = ((total_sales - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
    
    # Get recent orders
    recent_orders = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).order_by('-order_date')[:10]
    
    # Add status colors to orders
    status_colors = {
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'cancelled': 'danger'
    }
    
    for order in recent_orders:
        order.status_color = status_colors.get(order.status, 'secondary')
        order.total_items = order.items.count()
        order.customer_name = order.customer_name or order.customer_email

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_items': total_items,
        'average_order_value': average_order_value,
        'growth_rate': growth_rate,
        'status_breakdown': sales_summary['status_breakdown'],
        'daily_sales': daily_summary['daily_sales'],
        'recent_orders': recent_orders,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finance/sales_report.html', context)

@user_passes_test(is_superuser)
def product_report(request):
    """Product-wise sales report"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = timezone.datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = timezone.datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass

    # Get product summary
    product_summary = FinancialCalculationService.get_product_sales_summary(start_date, end_date)
    
    # Calculate additional metrics
    total_products = len(product_summary['product_sales'])
    active_products = sum(1 for data in product_summary['product_sales'].values() if data['quantity_sold'] > 0)
    total_sold = sum(data['quantity_sold'] for data in product_summary['product_sales'].values())
    total_revenue = sum(data['total_sales'] for data in product_summary['product_sales'].values())
    
    # Calculate growth rate (comparing with previous period)
    previous_start = start_date - (end_date - start_date)
    previous_summary = FinancialCalculationService.get_product_sales_summary(previous_start, start_date)
    previous_revenue = sum(data['total_sales'] for data in previous_summary['product_sales'].values())
    growth_rate = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    
    # Get category data for the pie chart
    category_data = {}
    for data in product_summary['product_sales'].values():
        category = data['product'].category
        if category.name not in category_data:
            category_data[category.name] = 0
        category_data[category.name] += data['total_sales']
    
    # Sort products by revenue for top products
    top_products = sorted(
        product_summary['product_sales'].values(),
        key=lambda x: x['total_sales'],
        reverse=True
    )
    
    # Add stock status to products
    for product_data in top_products:
        product = product_data['product']
        if product.stock <= 0:
            product_data['stock_status'] = 'Out of Stock'
            product_data['stock_status_color'] = 'danger'
        elif product.stock < 10:
            product_data['stock_status'] = 'Low Stock'
            product_data['stock_status_color'] = 'warning'
        else:
            product_data['stock_status'] = 'In Stock'
            product_data['stock_status_color'] = 'success'

    context = {
        'total_products': total_products,
        'active_products': active_products,
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'growth_rate': growth_rate,
        'category_data': [{'name': name, 'sales': sales} for name, sales in category_data.items()],
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finance/product_report.html', context)

@user_passes_test(is_superuser)
def profit_report(request):
    """Profit and loss report"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = timezone.datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = timezone.datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass

    profit_summary = FinancialCalculationService.get_profit_summary(start_date, end_date)
    payment_summary = FinancialCalculationService.get_payment_summary(start_date, end_date)
    
    # Calculate margin percentage
    if profit_summary['total_sales'] > 0:
        margin_percentage = (profit_summary['gross_profit'] / profit_summary['total_sales']) * 100
    else:
        margin_percentage = 0
    
    # Add margin percentage to profit summary
    profit_summary['margin_percentage'] = margin_percentage

    # Get category breakdown
    orders = Order.objects.filter(
        order_date__date__range=[start_date, end_date],
        status__in=['delivered', 'shipped']
    )
    
    category_breakdown = {}
    for order in orders:
        for item in order.items.all():
            category = item.product.category.name
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'sales': Decimal('0'),
                    'cost': Decimal('0'),
                    'gross_profit': Decimal('0'),
                    'margin': Decimal('0')
                }
            
            sales = item.quantity * item.unit_price
            cost = item.quantity * item.product.buying_price
            gross_profit = sales - cost
            
            category_breakdown[category]['sales'] += sales
            category_breakdown[category]['cost'] += cost
            category_breakdown[category]['gross_profit'] += gross_profit
    
    # Calculate margins for each category
    for category in category_breakdown:
        if category_breakdown[category]['sales'] > 0:
            category_breakdown[category]['margin'] = (
                category_breakdown[category]['gross_profit'] / 
                category_breakdown[category]['sales'] * 100
            )
    
    # Add category breakdown to profit summary
    profit_summary['category_breakdown'] = category_breakdown

    context = {
        'profit_summary': profit_summary,
        'payment_summary': payment_summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finance/profit_report.html', context)

@user_passes_test(is_superuser)
def expense_report(request):
    """Detailed expense report"""
    # Implementation

@user_passes_test(is_superuser)
def profit_loss(request):
    """Profit and Loss statement"""
    # Implementation

@user_passes_test(is_superuser)
def balance_sheet(request):
    """Balance Sheet report"""
    # Implementation

@user_passes_test(is_superuser)
def cash_flow(request):
    """Cash Flow statement"""
    # Implementation