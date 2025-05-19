from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
from datetime import timedelta

class AdminActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('user_management', 'User Management'),
        ('settings_update', 'Settings Update'),
        ('order_management', 'Order Management'),
        ('inventory_update', 'Inventory Update'),
        ('system_config', 'System Configuration'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Admin Activity')
        verbose_name_plural = _('Admin Activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin.username} - {self.activity_type} - {self.created_at}"

class SystemNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('system_alert', 'System Alert'),
        ('security_alert', 'Security Alert'),
        ('inventory_alert', 'Inventory Alert'),
        ('order_alert', 'Order Alert'),
        ('user_alert', 'User Alert'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name='read_notifications', blank=True)

    class Meta:
        verbose_name = _('System Notification')
        verbose_name_plural = _('System Notifications')
        ordering = ['-created_at', '-priority']

    def __str__(self):
        return f"{self.notification_type} - {self.title} - {self.priority}"

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_settings')
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')
        ordering = ['key']

    def __str__(self):
        return f"{self.key} - {self.value[:50]}"

class FinancialTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('salary', 'Salary'),
        ('expense', 'Expense'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card'),
        ('mobile_banking', 'Mobile Banking'),
        ('other', 'Other'),
    ]
    
    date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Financial Transaction')
        verbose_name_plural = _('Financial Transactions')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.date}"

class ProductAnalytics(models.Model):
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE, related_name='analytics')
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

class MonthlyReport(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_advertisement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Monthly Report')
        verbose_name_plural = _('Monthly Reports')
        ordering = ['-year', '-month']
        unique_together = ['year', 'month']

    @property
    def gross_profit(self):
        return self.total_sales - self.total_cost

    @property
    def net_profit(self):
        return (self.total_sales - self.total_cost - 
                self.total_expenses - self.total_advertisement - 
                self.total_salary)

    @property
    def profit_margin(self):
        if self.total_sales > 0:
            return (self.net_profit / self.total_sales) * 100
        return 0

    def __str__(self):
        return f"Report for {self.year}-{self.month:02d}"

    @classmethod
    def generate_monthly_report(cls, year, month):
        """Generate or update monthly report from daily sales data"""
        start_date = timezone.datetime(year, month, 1).date()
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1).date() - timedelta(days=1)

        daily_sales = DailySales.objects.filter(
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

        report, created = cls.objects.update_or_create(
            year=year,
            month=month,
            defaults={
                'total_sales': daily_sales['total_sales'] or 0,
                'total_orders': daily_sales['total_orders'] or 0,
                'total_cost': daily_sales['total_cost'] or 0,
                'total_expenses': daily_sales['total_expenses'] or 0,
                'total_advertisement': daily_sales['total_advertisement'] or 0,
                'total_salary': daily_sales['total_salary'] or 0,
            }
        )
        return report
