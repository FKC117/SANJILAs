from django.contrib import admin
from .models import Order, OrderItem, ShippingRate, StockMovement

# Register your models here.

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'is_preorder']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_phone', 'total_amount', 'order_date', 'status']
    list_filter = ['status', 'order_date', 'shipping_location']
    search_fields = ['customer_name', 'customer_phone', 'id']
    readonly_fields = ['order_date']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'city', 'zone', 'area', 'shipping_location', 'shipping_cost')
        }),
        ('Order Details', {
            'fields': ('order_date', 'status', 'total_amount', 'payment_method', 'payment_status', 'order_notes')
        })
    )

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name']

admin.site.register(StockMovement)
