# accounts/accounting_utils.py

from django.db.models import Sum, F
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Revenue, Expense, Receivable, Payable,
    Account, ExpenseCategory
)
from shop.models import Product
from order.models import Order, OrderItem

class AccountingCalculator:
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date or (timezone.now() - timedelta(days=30)).date()
        self.end_date = end_date or timezone.now().date()
        self._orders = None
        self._revenue_data = None
        self._expense_data = None
        self._profit_data = None
        self._balance_sheet = None

    @property
    def orders(self):
        if self._orders is None:
            self._orders = Order.objects.filter(
                order_date__range=[self.start_date, self.end_date],
                status__in=['delivered', 'shipped', 'pending']
            )
        return self._orders

    def calculate_revenue(self):
        """Calculate all revenue components"""
        if self._revenue_data is None:
            # Product sales (excluding shipping)
            product_sales = self.orders.aggregate(
                total=Sum(F('total_amount') - F('shipping_cost'))
            )['total'] or Decimal('0')

            # Manual revenue entries
            manual_revenue = Revenue.objects.filter(
                date__range=[self.start_date, self.end_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            self._revenue_data = {
                'product_sales': product_sales,
                'manual_revenue': manual_revenue,
                'total_revenue': product_sales + manual_revenue
            }
        return self._revenue_data

    def calculate_expenses(self):
        """Calculate all expense components"""
        if self._expense_data is None:
            # Cost of goods sold
            cost_of_goods = OrderItem.objects.filter(
                order__in=self.orders
            ).aggregate(
                total=Sum(F('quantity') * F('product__buying_price'))
            )['total'] or Decimal('0')

            # Shipping expenses
            shipping_expense = self.orders.aggregate(
                total=Sum('shipping_cost')
            )['total'] or Decimal('0')

            # COD charges (0.5% of product price for COD orders)
            cod_charges = self.orders.filter(
                payment_method__in=['cash', 'cash_on_delivery']
            ).aggregate(
                total=Sum(F('total_amount') - F('shipping_cost')) * Decimal('0.005')
            )['total'] or Decimal('0')

            # Category expenses
            category_expenses = {}
            for category in ExpenseCategory.objects.filter(is_active=True):
                key = f"{category.name.lower().replace(' ', '_')}_expenses"
                category_expenses[key] = Expense.objects.filter(
                    date__range=[self.start_date, self.end_date],
                    expense_category=category
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            self._expense_data = {
                'cost_of_goods': cost_of_goods,
                'shipping_expenses': shipping_expense,
                'cod_charges': cod_charges,
                **category_expenses,
                'total_expenses': cost_of_goods + shipping_expense + cod_charges + sum(category_expenses.values())
            }
        return self._expense_data

    def calculate_profits(self):
        """Calculate profit metrics"""
        if self._profit_data is None:
            revenue = self.calculate_revenue()
            expenses = self.calculate_expenses()

            gross_profit = revenue['total_revenue'] - expenses['cost_of_goods']
            net_profit = gross_profit - (expenses['total_expenses'] - expenses['cost_of_goods'])

            self._profit_data = {
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'profit_margin': (net_profit / revenue['total_revenue'] * 100) if revenue['total_revenue'] else 0
            }
        return self._profit_data

    def calculate_balance_sheet(self):
        """Calculate balance sheet components"""
        if self._balance_sheet is None:
            self._balance_sheet = {
                'assets': {
                    'cash': Account.objects.filter(type='asset', name='Cash').first().balance or Decimal('0'),
                    'accounts_receivable': Receivable.objects.filter(
                        status__in=['PENDING', 'PARTIAL', 'OVERDUE']
                    ).aggregate(
                        total=Sum('amount') - Sum('paid_amount')
                    )['total'] or Decimal('0'),
                    'inventory': Product.objects.aggregate(
                        total=Sum(F('stock') * F('buying_price'))
                    )['total'] or Decimal('0'),
                    'prepaid_expenses': Account.objects.filter(type='asset', name='Prepaid Expenses').first().balance or Decimal('0')
                },
                'liabilities': {
                    'accounts_payable': Payable.objects.filter(
                        status__in=['PENDING', 'PARTIAL', 'OVERDUE']
                    ).aggregate(
                        total=Sum('amount') - Sum('paid_amount')
                    )['total'] or Decimal('0'),
                    'sales_tax_payable': Account.objects.filter(type='liability', name='Sales Tax Payable').first().balance or Decimal('0'),
                    'wages_payable': Account.objects.filter(type='liability', name='Wages Payable').first().balance or Decimal('0')
                },
                'equity': {
                    'common_stock': Account.objects.filter(type='equity', name='Common Stock').first().balance or Decimal('0'),
                    'retained_earnings': Account.objects.filter(type='equity', name='Retained Earnings').first().balance or Decimal('0')
                }
            }

            # Calculate totals
            self._balance_sheet['total_assets'] = sum(self._balance_sheet['assets'].values())
            self._balance_sheet['total_liabilities'] = sum(self._balance_sheet['liabilities'].values())
            self._balance_sheet['total_equity'] = sum(self._balance_sheet['equity'].values())

        return self._balance_sheet

    def get_all_calculations(self):
        """Get all calculations in one call"""
        return {
            'revenue': self.calculate_revenue(),
            'expenses': self.calculate_expenses(),
            'profits': self.calculate_profits(),
            'balance_sheet': self.calculate_balance_sheet()
        }