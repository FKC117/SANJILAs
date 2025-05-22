from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import FileResponse, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django import forms
from .models import Order, OrderItem, ShippingRate, StockMovement

# Register your models here.

class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    method = forms.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    notes = forms.CharField(widget=forms.Textarea, required=False)

class DiscountForm(forms.Form):
    discount_type = forms.ChoiceField(choices=[
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount')
    ])
    discount_value = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = forms.CharField(widget=forms.Textarea, required=False)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'is_preorder', 'tags', 'notes', 'get_total_price')
    readonly_fields = ('get_total_price',)

    def get_total_price(self, obj):
        if obj.pk is None:  # New item
            return '-'
        try:
            return f"৳{obj.get_total_price()}"
        except (TypeError, AttributeError):
            return '-'
    get_total_price.short_description = 'Total Price'

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'unit_price':
            formfield.initial = 0
        elif db_field.name == 'quantity':
            formfield.initial = 1
        return formfield

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is None:  # Creating new order
            formset.form.base_fields['unit_price'].initial = 0
            formset.form.base_fields['quantity'].initial = 1
        return formset

@admin.action(description="Generate Invoice PDF")
def generate_invoice(modeladmin, request, queryset):
    for order in queryset:
        if not order.invoice_generated:
            try:
                order.generate_invoice_pdf()
                modeladmin.message_user(request, f"Invoice generated for Order #{order.id}")
            except Exception as e:
                modeladmin.message_user(request, f"Error generating invoice for Order #{order.id}: {str(e)}", level='error')

@admin.action(description="Regenerate Invoice PDF")
def regenerate_invoice(modeladmin, request, queryset):
    for order in queryset:
        try:
            order.generate_invoice_pdf(force_regenerate=True)
            modeladmin.message_user(request, f"Invoice regenerated for Order #{order.id}")
        except Exception as e:
            modeladmin.message_user(request, f"Error regenerating invoice for Order #{order.id}: {str(e)}", level='error')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_amount', 'payment_status', 'status', 
                   'order_date', 'payment_due', 'get_payment_summary', 'get_discount_summary',
                   'invoice_status', 'invoice_download', 'get_invoice_url')
    list_filter = ('status', 'payment_status', 'payment_method', 'order_date', 'invoice_generated')
    search_fields = ('customer_name', 'customer_phone', 'customer_email', 'invoice_number')
    readonly_fields = ('invoice_number', 'invoice_date', 'invoice_generated', 'payment_due', 'total_amount')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'city', 'zone', 'area', 
                      'city_name', 'zone_name', 'area_name', 'shipping_location', 'shipping_cost')
        }),
        ('Order Details', {
            'fields': ('status', 'order_notes', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'advance_payment', 
                      'payment_collected', 'payment_due', 'payment_notes')
        }),
        ('Discount Information', {
            'fields': ('discount_percentage', 'discount_amount')
        }),
        ('Invoice Information', {
            'fields': ('invoice_number', 'invoice_date', 'invoice_generated', 
                      'invoice_file', 'invoice_notes'),
            'classes': ('collapse',)
        }),
    )
    actions = ['generate_invoices', 'regenerate_invoices', 'mark_as_paid', 'mark_as_processing', 
              'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def save_model(self, request, obj, form, change):
        """Override save_model to handle initial save"""
        if not change:  # Creating new order
            obj.total_amount = 0  # Set initial total
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Override save_formset to handle inline items"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not change:  # New order
                instance.order = form.instance
            instance.save()
        formset.save_m2m()

    def get_payment_summary(self, obj):
        total_paid = obj.advance_payment + obj.payment_collected
        return format_html(
            '<span style="color: {};">৳{}</span> / ৳{}',
            'green' if total_paid >= obj.total_amount else 'orange',
            total_paid,
            obj.total_amount
        )
    get_payment_summary.short_description = 'Payment Summary'

    def get_discount_summary(self, obj):
        if obj.discount_amount > 0 or obj.discount_percentage > 0:
            return format_html(
                '{}% (৳{})',
                obj.discount_percentage,
                obj.discount_amount
            )
        return '-'
    get_discount_summary.short_description = 'Discount'

    def invoice_status(self, obj):
        if obj.invoice_generated:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.get_invoice_status_display()
            )
        return format_html(
            '<span style="color: red;">✗ Not Generated</span>'
        )
    invoice_status.short_description = 'Invoice Status'

    def invoice_download(self, obj):
        if obj.invoice_file:
            download_url = reverse('admin:download_invoice', args=[obj.id])
            view_url = reverse('view_invoice', args=[obj.id])
            return format_html(
                '<a class="button" href="{}">Download</a> | '
                '<a class="button" href="{}" target="_blank">View</a>',
                download_url, view_url
            )
        return "No invoice available"
    invoice_download.short_description = 'Invoice'

    def download_invoice(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if order.invoice_file:
            response = FileResponse(order.invoice_file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="invoice_{order.invoice_number}.pdf"'
            return response
        self.message_user(request, "No invoice file available", level='error')
        return self.response_change(request, order)

    def add_payment_view(self, request, order_id):
        order = self.get_object(request, order_id)
        if request.method == 'POST':
            form = PaymentForm(request.POST)
            if form.is_valid():
                try:
                    payment = order.add_payment(
                        amount=form.cleaned_data['amount'],
                        method=form.cleaned_data['method'],
                        notes=form.cleaned_data['notes'],
                        user=request.user
                    )
                    messages.success(request, f'Payment of ৳{payment["amount"]} recorded successfully.')
                    return HttpResponseRedirect(request.path)
                except ValueError as e:
                    messages.error(request, str(e))
        else:
            form = PaymentForm(initial={'method': order.payment_method})
        
        return render(request, 'admin/order/add_payment.html', {
            'form': form,
            'order': order,
            'title': f'Add Payment for Order #{order.id}',
            'payment_summary': order.get_payment_summary()
        })

    def add_discount_view(self, request, order_id):
        order = self.get_object(request, order_id)
        if request.method == 'POST':
            form = DiscountForm(request.POST)
            if form.is_valid():
                if form.cleaned_data['discount_type'] == 'percentage':
                    order.discount_percentage = form.cleaned_data['discount_value']
                    order.discount_amount = 0
                else:
                    order.discount_amount = form.cleaned_data['discount_value']
                    order.discount_percentage = 0
                order.save()
                messages.success(request, 'Discount applied successfully.')
                return HttpResponseRedirect(request.path)
        else:
            form = DiscountForm(initial={
                'discount_type': 'percentage' if order.discount_percentage > 0 else 'amount',
                'discount_value': order.discount_percentage or order.discount_amount
            })
        
        return render(request, 'admin/order/add_discount.html', {
            'form': form,
            'order': order,
            'title': f'Add Discount for Order #{order.id}',
            'discount_summary': order.get_discount_summary()
        })

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:order_id>/add-payment/', 
                 self.admin_site.admin_view(self.add_payment_view),
                 name='order-add-payment'),
            path('<path:order_id>/add-discount/',
                 self.admin_site.admin_view(self.add_discount_view),
                 name='order-add-discount'),
            path('<path:order_id>/download-invoice/',
                 self.admin_site.admin_view(self.download_invoice),
                 name='download_invoice'),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        order = self.get_object(request, object_id)
        extra_context.update({
            'payment_summary': order.get_payment_summary(),
            'discount_summary': order.get_discount_summary(),
            'show_payment_button': order.payment_due > 0,
            'show_discount_button': True,
        })
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        if "_add-payment" in request.POST:
            return HttpResponseRedirect(
                reverse('admin:order-add-payment', args=[obj.pk])
            )
        if "_add-discount" in request.POST:
            return HttpResponseRedirect(
                reverse('admin:order-add-discount', args=[obj.pk])
            )
        return super().response_change(request, obj)

    @admin.action(description="Generate Invoices")
    def generate_invoices(self, request, queryset):
        for order in queryset:
            if not order.invoice_generated:
                try:
                    order.generate_invoice_pdf()
                    self.message_user(request, f"Invoice generated for Order #{order.id}")
                except Exception as e:
                    self.message_user(request, f"Error generating invoice for Order #{order.id}: {str(e)}", level='error')

    @admin.action(description="Regenerate Invoices")
    def regenerate_invoices(self, request, queryset):
        for order in queryset:
            try:
                order.generate_invoice_pdf(force_regenerate=True)
                self.message_user(request, f"Invoice regenerated for Order #{order.id}")
            except Exception as e:
                self.message_user(request, f"Error regenerating invoice for Order #{order.id}: {str(e)}", level='error')

    def get_invoice_url(self, obj):
        if obj.invoice_generated:
            url = reverse('view_invoice', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank">View Invoice</a>',
                url
            )
        return "-"
    get_invoice_url.short_description = 'Invoice URL'
    get_invoice_url.allow_tags = True

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name']

admin.site.register(StockMovement)


