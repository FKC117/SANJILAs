from django.contrib import admin
from .models import *
#from django_summernote.admin import SummernoteModelAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from django.shortcuts import render
from django.db.models import Sum


class HeroImageInline(admin.TabularInline):
    model = HeroImage
    extra = 3
    ordering = ('order',)

class HeroContentAdmin(admin.ModelAdmin):
    inlines = [HeroImageInline]
    list_display = ('title', 'publish', 'subtitle')
    list_editable = ('publish',)
 
admin.site.register(HeroContent, HeroContentAdmin)
admin.site.register(HeroImage) # Optional 

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
class ProductSupplierInline(admin.TabularInline):
    model = ProductSupplier
    extra = 1
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductSupplierInline]
    list_display = ('name', 'sku', 'category', 'subcategory', 'show_price', 'selling_price', 'discount_price', 'discount_percentage', 'margin', 'available', 'stock', 'preorder', 'preorder_delivery_time')
    list_display_links = ('name', 'sku')
    list_editable = ('selling_price', 'discount_percentage', 'discount_price', 'show_price', 'stock', 'preorder', 'preorder_delivery_time')
    list_filter = ('suppliers', 'category', 'subcategory', 'available', 'featured', 'best_selling', 'trending', 'new_arrival', 'preorder')
    # filter_horizontal = ('suppliers',)
    search_fields = ('name', 'category__name', 'subcategory__name', 'sku')
    list_per_page = 20
    ordering = ('-id',)
    prepopulated_fields = {'slug': ('name',)}
    actions = ['view_supplier_prices']

    def view_supplier_prices(self, request, queryset):
        product_supplier_data = []
        for product in queryset:
            suppliers_data = ProductSupplier.objects.filter(product=product).select_related('supplier')
            product_supplier_data.append({
                'product': product,
                'suppliers': suppliers_data
            })
        context = {'product_supplier_data': product_supplier_data}
        return render(request, 'shop/admin/view_supplier_prices.html', context)
    view_supplier_prices.short_description = "View Supplier Prices"

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'country')
    # filter_horizontal = ('product',)
    list_filter = ('country',)
    search_fields = ('name', 'email', 'phone')
    list_per_page = 20
    # actions = ['view_supplied_products_details']

    # def view_supplied_products_details(self, request, queryset):
    #     supplier_product_data = []
    #     for supplier in queryset:
    #         products_data = []
    #         product_suppliers = ProductSupplier.objects.filter(supplier=supplier).select_related('product')
    #         for ps in product_suppliers:
    #             # Get the first image of the product
    #             first_image_url = ps.product.first_image()

    #             # Calculate total received quantity from this supplier
    #             total_received = StockMovement.objects.filter(
    #                 product=ps.product,
    #                 purchase_order__purchaseorderitem__product=ps.product,
    #                 purchase_order__purchaseorderitem__purchase_order__supplier=supplier,
    #                 type='PURCHASE_ORDER_IN'
    #             ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    #             products_data.append({
    #                 'product': ps.product,
    #                 'first_image_url': first_image_url,
    #                 'buying_price': ps.buying_price,
    #                 'total_received': total_received,
    #             })

    #         supplier_product_data.append({
    #             'supplier': supplier,
    #             'products': products_data,
    #         })

    #     context = {'supplier_product_data': supplier_product_data}
    #     return render(request, 'shop/admin/view_supplied_products_details.html', context)
    # view_supplied_products_details.short_description = "View Supplied Products Details"

 
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage) # Optional
admin.site.register(Supplier, SupplierAdmin)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_description')
        }),
        ('Logos', {
            'fields': ('navbar_logo', 'footer_logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'youtube_url', 'threads_url')
        }),
        ('SEO & Analytics', {
            'fields': ('meta_keywords', 'meta_description', 'google_analytics_id', 'meta_pixel_id'),
            'description': 'Add your tracking IDs for Google Analytics and Meta Pixel'
        }),
        ('Footer', {
            'fields': ('footer_text', 'copyright_text')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance of SiteSettings
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only instance
        return False
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add preview for logo fields
        if obj:
            for field in ['navbar_logo', 'footer_logo', 'favicon']:
                if getattr(obj, field):
                    form.base_fields[field].help_text = format_html(
                        '<img src="{}" style="max-height: 50px; margin-top: 10px;" />',
                        getattr(obj, field).url
                    )
        return form

@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one instance
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    list_editable = ('is_read',)
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True