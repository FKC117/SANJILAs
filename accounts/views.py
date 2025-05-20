from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Sum, Count, Avg, ExpressionWrapper, FloatField, F
from django.db.models.functions import Cast, TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from .models import (
    FinancialTransaction, ProductAnalytics, DailySales, 
    MonthlyReport, AdminActivity, SystemNotification,
    Account, Transaction, JournalEntry, JournalEntryLine,
    Receivable, Payable, Expense, Revenue,
    ProfitLossReport, BalanceSheetReport, AccountCategory
)
from shop.models import Product
from order.models import Order, OrderItem
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
from .forms import JournalEntryForm, ReceivableForm, PayableForm, ExpenseForm, RevenueForm, AccountForm, AccountCategoryForm

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def product_dashboard(request):
    """Product management dashboard for superusers"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('shop:home')
        
    # Get date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    current_month = today.month
    current_year = today.year

    # Get recent activities
    recent_activities = AdminActivity.objects.all()[:10]
    recent_notifications = SystemNotification.objects.filter(
        is_read=False
    ).order_by('-created_at', '-priority')[:5]

    # Get financial summary
    financial_summary = {
        'today': get_daily_summary(today),
        'month': get_monthly_summary(current_year, current_month),
        'thirty_days': get_period_summary(thirty_days_ago, today),
    }

    # Get product analytics
    product_analytics = get_product_analytics()

    # Get sales trends
    sales_trends = get_sales_trends(thirty_days_ago, today)

    # Get expense breakdown
    expense_breakdown = get_expense_breakdown(thirty_days_ago, today)

    # Get all products for management
    products = Product.objects.all().order_by('-created_at')

    context = {
        'financial_summary': financial_summary,
        'product_analytics': product_analytics,
        'sales_trends': sales_trends,
        'expense_breakdown': expense_breakdown,
        'recent_activities': recent_activities,
        'recent_notifications': recent_notifications,
        'today': today,
        'products': products,
    }
    return render(request, 'accounts/product_dashboard.html', context)

def get_date_range(request):
    """Helper function to get date range from request parameters"""
    print("1. Starting get_date_range")
    try:
        if 'from_date' in request.GET and 'to_date' in request.GET:
            print("2a. Using from_date and to_date parameters")
            try:
                from_date = datetime.strptime(request.GET['from_date'], '%Y-%m-%d').date()
                to_date = datetime.strptime(request.GET['to_date'], '%Y-%m-%d').date()
                print(f"2b. Parsed dates: from_date={from_date}, to_date={to_date}")
                return from_date, to_date
            except ValueError as date_error:
                print(f"2c. Date parsing error: {str(date_error)}")
                raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {str(date_error)}")
        
        # Default to last 30 days if no valid dates provided
        print("3a. Using days parameter")
        try:
            days = int(request.GET.get('days', 30))
            print(f"3b. Days parameter: {days}")
            if days <= 0:
                raise ValueError("Days parameter must be greater than 0")
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            print(f"3c. Calculated date range: start_date={start_date}, end_date={end_date}")
            return start_date, end_date
        except ValueError as days_error:
            print(f"3d. Days parameter error: {str(days_error)}")
            raise ValueError(f"Invalid days parameter. Must be a positive integer. Error: {str(days_error)}")
    except Exception as e:
        print(f"ERROR in get_date_range: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

@user_passes_test(is_superuser)
def get_sales_data(request):
    """View to get sales data with date filtering"""
    try:
        print("1. Starting get_sales_data view")
        start_date, end_date = get_date_range(request)
        print(f"2. Date range: {start_date} to {end_date}")

        # Convert dates to timezone-aware datetimes
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        # Get daily sales data
        print("3. Querying daily sales data...")
        try:
            # Get sales breakdown by status
            status_breakdown = Order.objects.filter(
                order_date__range=[start_datetime, end_datetime],
                status__in=['delivered', 'shipped', 'pending']
            ).values('status').annotate(
                total_sales=Sum('total_amount'),
                order_count=Count('id')
            )
            
            # Initialize status totals
            status_totals = {
                'delivered': {'sales': Decimal('0'), 'orders': 0},
                'shipped': {'sales': Decimal('0'), 'orders': 0},
                'pending': {'sales': Decimal('0'), 'orders': 0}
            }
            
            # Calculate totals by status
            for item in status_breakdown:
                status = item['status']
                status_totals[status]['sales'] = Decimal(str(item['total_sales'] or 0))
                status_totals[status]['orders'] = item['order_count']

            # Get daily data
            daily_data = Order.objects.filter(
                order_date__range=[start_datetime, end_datetime],
                status__in=['delivered', 'shipped', 'pending']
            ).values('order_date').annotate(
                sales=Sum('total_amount'),
                orders=Count('id')
            ).order_by('order_date')
            print(f"4. Found {len(daily_data)} daily records")
        except Exception as query_error:
            print(f"4a. Query error: {str(query_error)}")
            print(f"4b. Query error type: {type(query_error)}")
            import traceback
            print(f"4c. Query traceback: {traceback.format_exc()}")
            raise

        # Calculate total sales and orders
        total_sales = Decimal('0')
        total_orders = 0
        for item in daily_data:
            total_sales += Decimal(str(item['sales'] or 0))
            total_orders += item['orders']
        print(f"5. Total sales: {total_sales}, Total orders: {total_orders}")

        # Get expenses for the period
        print("6. Getting expense breakdown...")
        try:
            expenses = get_expense_breakdown(start_date, end_date)
            total_expenses = Decimal(str(sum(expenses.values())))
            print(f"7. Total expenses: {total_expenses}")
        except Exception as expense_error:
            print(f"7a. Expense error: {str(expense_error)}")
            print(f"7b. Expense error type: {type(expense_error)}")
            import traceback
            print(f"7c. Expense traceback: {traceback.format_exc()}")
            raise

        # Calculate profits
        print("8. Calculating profits...")
        try:
            total_cost = OrderItem.objects.filter(
                order__order_date__range=[start_datetime, end_datetime],
                order__status__in=['delivered', 'shipped', 'pending']
            ).aggregate(
                total=Sum(F('quantity') * F('product__buying_price'))
            )['total'] or Decimal('0')
            print(f"9. Total cost: {total_cost}")
        except Exception as cost_error:
            print(f"9a. Cost calculation error: {str(cost_error)}")
            print(f"9b. Cost error type: {type(cost_error)}")
            import traceback
            print(f"9c. Cost traceback: {traceback.format_exc()}")
            raise

        # All calculations using Decimal
        gross_profit = total_sales - total_cost
        net_profit = gross_profit - total_expenses
        print(f"10. Gross profit: {gross_profit}, Net profit: {net_profit}")

        response_data = {
            'status': 'success',
            'data': {
                'daily_data': [
                    {
                        'date': item['order_date'].strftime('%Y-%m-%d'),
                        'sales': float(item['sales'] or 0),
                        'orders': item['orders']
                    }
                    for item in daily_data
                ],
                'summary': {
                    'total_sales': float(total_sales),
                    'total_orders': total_orders,
                    'total_cost': float(total_cost),
                    'gross_profit': float(gross_profit),
                    'net_profit': float(net_profit),
                    'total_expenses': float(total_expenses),
                    'expenses': {k: float(v) for k, v in expenses.items()},
                    'status_breakdown': {
                        status: {
                            'sales': float(data['sales']),
                            'orders': data['orders'],
                            'percentage': float(data['sales'] / total_sales * 100) if total_sales > 0 else 0
                        }
                        for status, data in status_totals.items()
                    }
                }
            }
        }
        print("11. Returning response")
        return JsonResponse(response_data)
    except Exception as e:
        print(f"ERROR in get_sales_data: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'error_type': str(type(e).__name__)
        }, status=400)

@user_passes_test(is_superuser)
def get_product_performance(request):
    """View to get product performance data with date filtering"""
    try:
        start_date, end_date = get_date_range(request)
        
        # Get product analytics data
        analytics_data = ProductAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).values(
            'product__name',
            'product__category__name'
        ).annotate(
            total_sales=Sum('total_sales'),
            total_quantity=Sum('quantity_sold'),
            total_cost=Sum('total_cost'),
            days_count=Count('date')
        ).order_by('-total_sales')

        if not analytics_data:
            return JsonResponse({
                'status': 'success',
                'data': {
                    'products': [],
                    'summary': {
                        'total_sales': 0,
                        'total_quantity': 0,
                        'total_cost': 0,
                        'gross_profit': 0,
                        'net_profit': 0,
                        'total_expenses': 0,
                        'expenses': get_expense_breakdown(start_date, end_date)
                    }
                }
            })

        # Process product data
        products = []
        total_sales = Decimal('0')
        total_cost = Decimal('0')
        total_quantity = 0

        for item in analytics_data:
            try:
                product_data = {
                    'name': item['product__name'],
                    'category': item['product__category__name'],
                    'total_sales': float(item['total_sales'] or 0),
                    'total_quantity': item['total_quantity'] or 0,
                    'total_cost': float(item['total_cost'] or 0),
                    'avg_daily_sales': float(item['total_sales'] or 0) / item['days_count'],
                    'avg_daily_quantity': (item['total_quantity'] or 0) / item['days_count']
                }
                product_data['profit'] = product_data['total_sales'] - product_data['total_cost']
                products.append(product_data)

                total_sales += Decimal(str(item['total_sales'] or 0))
                total_cost += Decimal(str(item['total_cost'] or 0))
                total_quantity += item['total_quantity'] or 0
            except (TypeError, ZeroDivisionError) as e:
                print(f"Error processing product {item['product__name']}: {str(e)}")
                continue

        # Calculate summary statistics
        expenses = get_expense_breakdown(start_date, end_date)
        total_expenses = sum(expenses.values())
        gross_profit = float(total_sales - total_cost)
        net_profit = gross_profit - total_expenses

        return JsonResponse({
            'status': 'success',
            'data': {
                'products': products,
                'summary': {
                    'total_sales': float(total_sales),
                    'total_quantity': total_quantity,
                    'total_cost': float(total_cost),
                    'gross_profit': gross_profit,
                    'net_profit': net_profit,
                    'total_expenses': total_expenses,
                    'expenses': expenses
                }
            }
        })
    except Exception as e:
        print(f"Error in get_product_performance: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def get_daily_summary(date):
    """Get summary of daily financial data"""
    try:
        daily = DailySales.objects.get(date=date)
        return {
            'total_sales': daily.total_sales,
            'total_orders': daily.total_orders,
            'gross_profit': daily.gross_profit,
            'net_profit': daily.net_profit,
            'expenses': daily.total_expenses + daily.total_advertisement + daily.total_salary,
        }
    except DailySales.DoesNotExist:
        return {
            'total_sales': 0,
            'total_orders': 0,
            'gross_profit': 0,
            'net_profit': 0,
            'expenses': 0,
        }

def get_monthly_summary(year, month):
    """Get summary of monthly financial data"""
    try:
        monthly = MonthlyReport.objects.get(year=year, month=month)
        return {
            'total_sales': monthly.total_sales,
            'total_orders': monthly.total_orders,
            'gross_profit': monthly.gross_profit,
            'net_profit': monthly.net_profit,
            'profit_margin': monthly.profit_margin,
            'expenses': monthly.total_expenses + monthly.total_advertisement + monthly.total_salary,
        }
    except MonthlyReport.DoesNotExist:
        return {
            'total_sales': 0,
            'total_orders': 0,
            'gross_profit': 0,
            'net_profit': 0,
            'profit_margin': 0,
            'expenses': 0,
        }

def get_period_summary(start_date, end_date):
    """Get summary of financial data for a date range"""
    # Get monthly reports for the period
    monthly_data = MonthlyReport.objects.filter(
        year__gte=start_date.year,
        year__lte=end_date.year,
        month__gte=start_date.month if start_date.year == end_date.year else 1,
        month__lte=end_date.month if start_date.year == end_date.year else 12
    ).aggregate(
        total_sales=Sum('total_sales'),
        total_orders=Sum('total_orders'),
        total_cost=Sum('total_cost'),
        total_expenses=Sum('total_expenses'),
        total_advertisement=Sum('total_advertisement'),
        total_salary=Sum('total_salary')
    )
    
    # Get daily sales for partial months
    daily_data = DailySales.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(
        total_sales=Sum('total_sales'),
        total_orders=Sum('total_orders'),
        total_cost=Sum('total_cost'),
        total_expenses=Sum('total_expenses'),
        total_advertisement=Sum('total_advertisement'),
        total_salary=Sum('total_salary')
    )

    # Combine monthly and daily data
    total_sales = (monthly_data['total_sales'] or 0) + (daily_data['total_sales'] or 0)
    total_cost = (monthly_data['total_cost'] or 0) + (daily_data['total_cost'] or 0)
    total_expenses = (
        (monthly_data['total_expenses'] or 0) + (daily_data['total_expenses'] or 0) +
        (monthly_data['total_advertisement'] or 0) + (daily_data['total_advertisement'] or 0) +
        (monthly_data['total_salary'] or 0) + (daily_data['total_salary'] or 0)
    )
    
    return {
        'total_sales': total_sales,
        'total_orders': (monthly_data['total_orders'] or 0) + (daily_data['total_orders'] or 0),
        'gross_profit': total_sales - total_cost,
        'net_profit': total_sales - total_cost - total_expenses,
        'expenses': total_expenses,
    }

def get_product_analytics():
    """Get top performing products"""
    return ProductAnalytics.objects.filter(
        date=timezone.now().date()
    ).select_related('product').order_by('-total_sales')[:10]

def get_sales_trends(start_date, end_date):
    """Get sales trends for the period"""
    # Get daily sales data
    daily_sales = DailySales.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date').values(
        'date', 'total_sales', 'total_orders'
    )

    # Get monthly sales data
    monthly_sales = MonthlyReport.objects.filter(
        year__gte=start_date.year,
        year__lte=end_date.year,
        month__gte=start_date.month if start_date.year == end_date.year else 1,
        month__lte=end_date.month if start_date.year == end_date.year else 12
    ).order_by('year', 'month').values(
        'year', 'month', 'total_sales', 'total_orders'
    )

    # Combine and format the data
    sales_data = []
    
    # Add daily sales
    for sale in daily_sales:
        sales_data.append({
            'date': sale['date'].strftime('%Y-%m-%d'),
            'sales': float(sale['total_sales'] or 0),
            'orders': sale['total_orders'] or 0
        })
    
    # Add monthly sales
    for sale in monthly_sales:
        sales_data.append({
            'date': f"{sale['year']}-{sale['month']:02d}-01",
            'sales': float(sale['total_sales'] or 0),
            'orders': sale['total_orders'] or 0
        })

    return sorted(sales_data, key=lambda x: x['date'])

def get_expense_breakdown(start_date, end_date):
    """Helper function to get expense breakdown for a date range"""
    # Get expenses from MonthlyReport
    monthly_expenses = MonthlyReport.objects.filter(
        year__gte=start_date.year,
        year__lte=end_date.year,
        month__gte=start_date.month if start_date.year == end_date.year else 1,
        month__lte=end_date.month if start_date.year == end_date.year else 12
    ).aggregate(
        salary=Sum('total_salary'),
        advertisement=Sum('total_advertisement'),
        shipping=Sum('total_cost')  # Using total_cost as shipping cost
    )

    # Get other expenses from FinancialTransaction
    other_expenses = FinancialTransaction.objects.filter(
        date__range=[start_date, end_date],
        transaction_type='expense'
    ).exclude(
        transaction_type__in=['salary', 'advertisement']
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Get salary expenses from FinancialTransaction
    salary_expenses = FinancialTransaction.objects.filter(
        date__range=[start_date, end_date],
        transaction_type='salary'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Get advertisement expenses from FinancialTransaction
    ad_expenses = FinancialTransaction.objects.filter(
        date__range=[start_date, end_date],
        transaction_type='advertisement'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Calculate total expenses
    total_expenses = {
        'salary': float(monthly_expenses['salary'] or 0) + float(salary_expenses),
        'advertisement': float(monthly_expenses['advertisement'] or 0) + float(ad_expenses),
        'shipping': float(monthly_expenses['shipping'] or 0),
        'other': float(other_expenses)
    }

    return total_expenses

@user_passes_test(is_superuser)
def accounting_dashboard(request):
    """Main accounting dashboard view"""
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get financial summary
    total_revenue = Revenue.objects.filter(
        date__range=[start_date, end_date]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Expense.objects.filter(
        date__range=[start_date, end_date]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total receivables (amount - paid_amount)
    total_receivables = Receivable.objects.filter(
        status__in=['PENDING', 'PARTIAL', 'OVERDUE']
    ).aggregate(
        total=Sum('amount') - Sum('paid_amount')
    )['total'] or 0
    
    # Calculate total payables (amount - paid_amount)
    total_payables = Payable.objects.filter(
        status__in=['PENDING', 'PARTIAL', 'OVERDUE']
    ).aggregate(
        total=Sum('amount') - Sum('paid_amount')
    )['total'] or 0
    
    # Get recent transactions
    recent_transactions = Transaction.objects.select_related(
        'account'
    ).order_by('-date', '-created_at')[:10]
    
    # Get monthly revenue trend
    monthly_revenue = Revenue.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')[:12]
    
    # Get expense breakdown
    expense_breakdown = Expense.objects.values(
        'type'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Get overdue receivables
    overdue_receivables = Receivable.objects.filter(
        status='OVERDUE'
    ).select_related('customer').order_by('due_date')[:5]
    
    # Get upcoming payables
    upcoming_payables = Payable.objects.filter(
        status__in=['PENDING', 'PARTIAL'],
        due_date__lte=end_date + timedelta(days=30)
    ).select_related('supplier').order_by('due_date')[:5]
    
    context = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'total_receivables': total_receivables,
        'total_payables': total_payables,
        'recent_transactions': recent_transactions,
        'monthly_revenue': monthly_revenue,
        'expense_breakdown': expense_breakdown,
        'overdue_receivables': overdue_receivables,
        'upcoming_payables': upcoming_payables,
    }
    
    return render(request, 'accounts/accounting_dashboard.html', context)

@login_required
def chart_of_accounts(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'category':
            form = AccountCategoryForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('accounts:chart_of_accounts')
        else:
            form = AccountForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('accounts:chart_of_accounts')
    else:
        form = AccountForm()
        category_form = AccountCategoryForm()

    # Get or create default categories for e-commerce
    default_categories = [
        {
            'name': 'Assets',
            'description': 'Resources owned by the business',
            'accounts': [
                {'name': 'Cash', 'code': '1000', 'type': 'asset', 'description': 'Cash in bank and on hand'},
                {'name': 'Accounts Receivable', 'code': '1100', 'type': 'asset', 'description': 'Amounts owed by customers'},
                {'name': 'Inventory', 'code': '1200', 'type': 'asset', 'description': 'Products available for sale'},
                {'name': 'Prepaid Expenses', 'code': '1300', 'type': 'asset', 'description': 'Expenses paid in advance'},
            ]
        },
        {
            'name': 'Liabilities',
            'description': 'Amounts owed to others',
            'accounts': [
                {'name': 'Accounts Payable', 'code': '2000', 'type': 'liability', 'description': 'Amounts owed to suppliers'},
                {'name': 'Sales Tax Payable', 'code': '2100', 'type': 'liability', 'description': 'Sales tax collected from customers'},
                {'name': 'Wages Payable', 'code': '2200', 'type': 'liability', 'description': 'Wages owed to employees'},
            ]
        },
        {
            'name': 'Equity',
            'description': 'Owner\'s interest in the business',
            'accounts': [
                {'name': 'Common Stock', 'code': '3000', 'type': 'equity', 'description': 'Owner\'s investment in the business'},
                {'name': 'Retained Earnings', 'code': '3100', 'type': 'equity', 'description': 'Accumulated profits'},
            ]
        },
        {
            'name': 'Revenue',
            'description': 'Income from business activities',
            'accounts': [
                {'name': 'Product Sales', 'code': '4000', 'type': 'revenue', 'description': 'Revenue from product sales'},
                {'name': 'Shipping Revenue', 'code': '4100', 'type': 'revenue', 'description': 'Revenue from shipping charges'},
                {'name': 'Service Revenue', 'code': '4200', 'type': 'revenue', 'description': 'Revenue from services'},
            ]
        },
        {
            'name': 'Expenses',
            'description': 'Costs incurred in running the business',
            'accounts': [
                {'name': 'Cost of Goods Sold', 'code': '5000', 'type': 'expense', 'description': 'Cost of products sold'},
                {'name': 'Shipping Expenses', 'code': '5100', 'type': 'expense', 'description': 'Cost of shipping products'},
                {'name': 'Marketing Expenses', 'code': '5200', 'type': 'expense', 'description': 'Advertising and promotion costs'},
                {'name': 'Payroll Expenses', 'code': '5300', 'type': 'expense', 'description': 'Employee wages and benefits'},
                {'name': 'Rent Expense', 'code': '5400', 'type': 'expense', 'description': 'Office and warehouse rent'},
                {'name': 'Utilities', 'code': '5500', 'type': 'expense', 'description': 'Electricity, water, and other utilities'},
                {'name': 'Website Expenses', 'code': '5600', 'type': 'expense', 'description': 'Website hosting and maintenance'},
                {'name': 'Payment Processing Fees', 'code': '5700', 'type': 'expense', 'description': 'Credit card and payment gateway fees'},
            ]
        }
    ]

    # Create default categories and accounts if they don't exist
    for category_data in default_categories:
        category, created = AccountCategory.objects.get_or_create(
            name=category_data['name'],
            defaults={'description': category_data['description']}
        )
        
        if created:
            for account_data in category_data['accounts']:
                Account.objects.create(
                    name=account_data['name'],
                    code=account_data['code'],
                    type=account_data['type'],
                    description=account_data['description'],
                    category=category
                )

    # Get all categories with their accounts
    account_categories = AccountCategory.objects.prefetch_related('accounts').all()

    return render(request, 'accounts/chart_of_accounts.html', {
        'form': form,
        'category_form': category_form,
        'account_categories': account_categories,
    })

@user_passes_test(is_superuser)
def journal_entries(request):
    """View for managing journal entries"""
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.created_by = request.user
            journal_entry.save()
            messages.success(request, 'Journal entry created successfully.')
            return redirect('accounts:journal_entries')
    else:
        form = JournalEntryForm()
    
    entries = JournalEntry.objects.select_related('created_by').prefetch_related('lines__account').order_by('-date', '-created_at')
    return render(request, 'accounts/journal_entries.html', {
        'form': form,
        'entries': entries
    })

@user_passes_test(is_superuser)
def receivables(request):
    """View for managing receivables"""
    if request.method == 'POST':
        form = ReceivableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Receivable created successfully.')
            return redirect('accounts:receivables')
    else:
        form = ReceivableForm()
    
    receivables = Receivable.objects.select_related('customer').order_by('-date', '-created_at')
    return render(request, 'accounts/receivables.html', {
        'form': form,
        'receivables': receivables
    })

@user_passes_test(is_superuser)
def payables(request):
    """View for managing payables"""
    if request.method == 'POST':
        form = PayableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payable created successfully.')
            return redirect('accounts:payables')
    else:
        form = PayableForm()
    
    payables = Payable.objects.select_related('supplier').order_by('-date', '-created_at')
    return render(request, 'accounts/payables.html', {
        'form': form,
        'payables': payables
    })

@user_passes_test(is_superuser)
def expenses(request):
    """View for managing expenses"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense created successfully.')
            return redirect('accounts:expenses')
    else:
        form = ExpenseForm()
    
    expenses = Expense.objects.select_related('account').order_by('-date', '-created_at')
    return render(request, 'accounts/expenses.html', {
        'form': form,
        'expenses': expenses
    })

@user_passes_test(is_superuser)
def revenue(request):
    """View for managing revenue"""
    if request.method == 'POST':
        form = RevenueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Revenue entry created successfully.')
            return redirect('accounts:revenue')
    else:
        form = RevenueForm()
    
    revenues = Revenue.objects.select_related('account').order_by('-date', '-created_at')
    return render(request, 'accounts/revenue.html', {
        'form': form,
        'revenues': revenues
    })

@user_passes_test(is_superuser)
def financial_reports(request):
    """View financial reports"""
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get P&L report
    pl_report = ProfitLossReport.objects.filter(
        start_date=start_date,
        end_date=end_date
    ).first()
    
    # Get Balance Sheet
    bs_report = BalanceSheetReport.objects.filter(
        start_date=start_date,
        end_date=end_date
    ).first()
    
    context = {
        'pl_report': pl_report,
        'bs_report': bs_report,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'accounts/financial_reports.html', context)
