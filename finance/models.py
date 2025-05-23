from django.db import models
from django.contrib.auth.models import User
from order.models import Order, OrderItem
from shop.models import Product
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

class FinancialYear(models.Model):
    """Track financial years for reporting"""
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

class Account(models.Model):
    """Chart of Accounts"""
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    """Financial Transactions"""
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('expense', 'Expense'),
        ('adjustment', 'Adjustment'),
    ]
    
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=50)  # Order number or invoice number
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class JournalEntry(models.Model):
    """Double-entry accounting entries"""
    date = models.DateField()
    reference = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class JournalEntryLine(models.Model):
    """Individual lines in a journal entry"""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True)

class ExpenseCategory(models.Model):
    """Expense categories for better tracking"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

class Expense(models.Model):
    """Track business expenses"""
    date = models.DateField()
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    reference = models.CharField(max_length=50, blank=True)  # Receipt/invoice number
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class FinancialReport(models.Model):
    """Base model for financial reports"""
    REPORT_TYPES = [
        ('pl', 'Profit & Loss'),
        ('bs', 'Balance Sheet'),
        ('cf', 'Cash Flow'),
    ]
    
    type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class ProductAnalytics(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    quantity_sold = models.PositiveIntegerField(default=0)
    quantity_purchased = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_level = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Product Analytics')
        verbose_name_plural = _('Product Analytics')
        ordering = ['-date', 'product']
        unique_together = ['product', 'date']

    @property
    def margin(self):
        if self.total_cost > 0:
            return ((self.total_sales - self.total_cost) / self.total_cost) * 100
        return 0

    @property
    def profit(self):
        return self.total_sales - self.total_cost

    def __str__(self):
        return f"{self.product.name} - {self.date}"

class DailySales(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_advertisement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _('Daily Sales')
        verbose_name_plural = _('Daily Sales')
        ordering = ['-date']

    @property
    def gross_profit(self):
        return self.total_sales - self.total_cost

    @property
    def net_profit(self):
        return (self.total_sales - self.total_cost - 
                self.total_expenses - self.total_advertisement - 
                self.total_salary)

    def __str__(self):
        return f"Sales for {self.date}"