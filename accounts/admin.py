from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import (
    AdminActivity, SystemNotification, SystemSettings,
    FinancialTransaction, ProductAnalytics, DailySales, MonthlyReport
)

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('admin', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at', 'admin')
    search_fields = ('admin__username', 'description', 'ip_address')
    readonly_fields = ('admin', 'activity_type', 'description', 'ip_address', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False  # Activities are created programmatically

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'title', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    list_editable = ('is_read', 'priority')
    readonly_fields = ('created_at',)
    filter_horizontal = ('read_by',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('read_by')

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'last_modified_by', 'last_modified_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('last_modified_by', 'last_modified_at')
    
    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

# Register new analytics and financial models
@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales', 'total_orders', 'total_cost', 'total_expenses', 'total_advertisement', 'total_salary')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)

@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'total_sales', 'total_orders', 'total_cost', 'total_expenses', 'total_advertisement', 'total_salary')
    list_filter = ('year', 'month')
    search_fields = ('year', 'month')
    ordering = ('-year', '-month')

@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'quantity_sold', 'total_sales', 'total_cost', 'stock_level')
    list_filter = ('date', 'product')
    search_fields = ('product__name',)
    ordering = ('-date', 'product')

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'amount', 'payment_method', 'created_by')
    list_filter = ('transaction_type', 'payment_method', 'date')
    search_fields = ('description', 'reference_number', 'created_by__username')
    ordering = ('-date',)
