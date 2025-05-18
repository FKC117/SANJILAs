from django.contrib import admin
from .models import (
    PathaoCredentials, PathaoToken, PathaoStore, PathaoCity,
    PathaoZone, PathaoArea, PathaoOrder
)

@admin.register(PathaoCredentials)
class PathaoCredentialsAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'default_username']
    readonly_fields = ['client_id', 'client_secret', 'default_username', 'default_password',
                      'test_client_id', 'test_client_secret', 'test_username', 'test_password']

@admin.register(PathaoToken)
class PathaoTokenAdmin(admin.ModelAdmin):
    list_display = ['access_token', 'expires_at', 'is_expired']
    readonly_fields = ['access_token', 'refresh_token', 'expires_at']
    list_filter = ['expires_at']

@admin.register(PathaoStore)
class PathaoStoreAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'store_id', 'city_id', 'zone_id', 'is_active', 'is_default_store']
    list_filter = ['is_active', 'is_default_store']
    search_fields = ['store_name', 'store_address']

@admin.register(PathaoCity)
class PathaoCityAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'city_id']
    search_fields = ['city_name']

@admin.register(PathaoZone)
class PathaoZoneAdmin(admin.ModelAdmin):
    list_display = ['zone_name', 'zone_id', 'city']
    list_filter = ['city']
    search_fields = ['zone_name', 'city__city_name']

@admin.register(PathaoArea)
class PathaoAreaAdmin(admin.ModelAdmin):
    list_display = ['area_name', 'area_id', 'zone', 'home_delivery_available', 'pickup_available']
    list_filter = ['home_delivery_available', 'pickup_available', 'zone__city']
    search_fields = ['area_name', 'zone__zone_name', 'zone__city__city_name']

@admin.register(PathaoOrder)
class PathaoOrderAdmin(admin.ModelAdmin):
    list_display = ['consignment_id', 'merchant_order_id', 'recipient_name', 'order_status', 'created_at']
    list_filter = ['order_status', 'delivery_type', 'created_at']
    search_fields = ['consignment_id', 'merchant_order_id', 'recipient_name', 'recipient_phone']
    readonly_fields = ['created_at', 'updated_at', 'pathao_updated_at']
    fieldsets = (
        ('Order Information', {
            'fields': ('consignment_id', 'merchant_order_id', 'store', 'order_status', 'order_status_slug')
        }),
        ('Recipient Details', {
            'fields': ('recipient_name', 'recipient_phone', 'recipient_address', 
                      'recipient_city', 'recipient_zone', 'recipient_area')
        }),
        ('Delivery Details', {
            'fields': ('delivery_type', 'item_type', 'special_instruction', 
                      'item_quantity', 'item_weight', 'item_description')
        }),
        ('Payment Information', {
            'fields': ('amount_to_collect', 'calculated_price', 'price_plan_id',
                      'cod_enabled', 'cod_percentage', 'additional_charge', 'final_price')
        }),
        ('Status Information', {
            'fields': ('invoice_id', 'pathao_updated_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
