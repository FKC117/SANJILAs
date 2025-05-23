from django.db import models
from shop.models import Product, SiteSettings
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
import os

from django.core.files import File
from django.urls import reverse
from django.utils import timezone
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from PIL import Image
import os.path
from django.core.mail import send_mail
from django.core.mail import EmailMessage

# Create your models here.
class ShippingRate(models.Model):
    """Model for different shipping rates based on location"""
    name = models.CharField(max_length=100)  # e.g., "Inside Dhaka", "Outside Dhaka"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Shipping Rate"
        verbose_name_plural = "Shipping Rates"

    def __str__(self):
        return f"{self.name} - ৳{self.price}"

    def get_absolute_url(self):
        return reverse('shipping_rates')

    @classmethod
    def get_rate(cls, location=None):
        """Get shipping rate based on location, or return default if no location specified"""
        try:
            if location == "inside_dhaka":
                try:
                    return cls.objects.get(name="Inside Dhaka").price
                except cls.DoesNotExist:
                    # Fall through to default handling
                    pass
            elif location == "outside_dhaka":
                try:
                    return cls.objects.get(name="Outside Dhaka").price
                except cls.DoesNotExist:
                    # Fall through to default handling
                    pass
            
            # Return default rate if specific rate not found
            try:
                return cls.objects.get(is_default=True).price
            except cls.DoesNotExist:
                # No default rate found, try first available rate
                first_rate = cls.objects.first()
                if first_rate:
                    return first_rate.price
                
                # Fallback to fixed price if no rates defined
                return 100  # Default fallback rate
        except Exception as e:
            # Log the error but provide a fallback to prevent site breaking
            print(f"Error retrieving shipping rate: {e}")
            return 100  # Default fallback rate if DB error

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('upay', 'Upay'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True, null=True)
    shipping_address = models.TextField(help_text="Enter the shipping address minimum 10 characters", validators=[MinLengthValidator(10)])
    city = models.CharField(max_length=50)  # Will store city_id
    zone = models.CharField(max_length=50, blank=True, null=True)  # Will store zone_id
    area = models.CharField(max_length=100, blank=True, null=True)  # Will store area_id
    city_name = models.CharField(max_length=100)  # For display purposes
    zone_name = models.CharField(max_length=100, blank=True, null=True)  # For display purposes
    area_name = models.CharField(max_length=100, blank=True, null=True)  # For display purposes
    shipping_location = models.CharField(max_length=50, choices=[
        ('inside_dhaka', 'Inside Dhaka'),
        ('outside_dhaka', 'Outside Dhaka')
    ], default='inside_dhaka')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_notes = models.TextField(blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    invoice_date = models.DateTimeField(null=True, blank=True)
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    invoice_generated = models.BooleanField(default=False)
    invoice_notes = models.TextField(blank=True, null=True)

    # Payment and Discount Fields
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
        help_text="Advance payment received")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Discount amount in currency")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
        help_text="Discount percentage (0-100)")
    payment_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Total payment collected so far")
    payment_due = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Remaining payment due")
    payment_history = models.JSONField(default=list, blank=True,
        help_text="History of payments made")
    payment_notes = models.TextField(blank=True, null=True,
        help_text="Notes about payments")

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

    def get_absolute_url(self):
        return reverse('view_invoice', kwargs={'order_id': self.id})

    @classmethod
    def print_payment_methods(cls):
        """Debug utility to print all payment methods used in orders"""
        payment_methods = cls.objects.values_list('payment_method', flat=True).distinct()
        print(f"All payment methods in database: {list(payment_methods)}")
        
        # Count orders by payment method
        for method in payment_methods:
            count = cls.objects.filter(payment_method=method).count()
            print(f"Payment method '{method}': {count} orders")
            
            # Show a sample order with this payment method
            sample = cls.objects.filter(payment_method=method).first()
            if sample:
                print(f"Sample order #{sample.id}: Total={sample.total_amount}, Shipping={sample.shipping_cost}")
                
        return list(payment_methods)

    def save(self, *args, **kwargs):
        if not self.pk:
            # First save, just to get a primary key
            self.total_amount = 0
            super().save(*args, **kwargs)
            return  # Don't try to access self.items.all() yet

        # Now safe to access related items
        subtotal = sum(item.get_total_price() for item in self.items.all())
        
        # Apply discount
        if self.discount_percentage > 0:
            discount = (subtotal * self.discount_percentage) / 100
            self.discount_amount = max(discount, self.discount_amount)
        
        # Calculate final total
        self.total_amount = subtotal - self.discount_amount + self.shipping_cost
        
        # Calculate payment due
        total_paid = self.advance_payment + self.payment_collected
        self.payment_due = self.total_amount - total_paid
        
        # Update payment status
        if self.payment_due <= 0:
            self.payment_status = 'paid'
        elif total_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'

        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXXXX
            date_str = timezone.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4().hex[:5]).upper()
            self.invoice_number = f"INV-{date_str}-{unique_id}"
            
            # Generate invoice PDF
            try:
                self.generate_invoice_pdf()
            except Exception as e:
                print(f"Error generating invoice PDF: {str(e)}")
            
            # Send invoice email if customer email is provided
            if self.customer_email:
                try:
                    self.send_invoice_email()
                except Exception as e:
                    print(f"Error sending invoice email: {str(e)}")
        
        # Save again with updated values
        super().save(*args, **kwargs)

    def generate_invoice_pdf(self, output_dir='invoices', force_regenerate=False):
        """Generate PDF invoice using ReportLab and update stock"""
        from django.db import transaction
        from django.core.files.base import ContentFile

        with transaction.atomic():
            # Check if invoice already exists and regeneration is not forced
            if self.invoice_generated and not force_regenerate:
                return self.invoice_file.path

            # Get site settings
            settings = SiteSettings.get_settings()
            
            # Prepare PDF in memory
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Define styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='RightAlign',
                parent=styles['Normal'],
                alignment=TA_RIGHT
            ))
            styles.add(ParagraphStyle(
                name='CenterAlign',
                parent=styles['Normal'],
                alignment=TA_CENTER
            ))
            styles.add(ParagraphStyle(
                name='InvoiceTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER
            ))
            
            # Draw logo if available (smaller size)
            if settings.navbar_logo:
                try:
                    logo_path = settings.navbar_logo.path
                    if os.path.exists(logo_path):
                        img = Image.open(logo_path)
                        # Calculate aspect ratio to maintain proportions
                        aspect = img.width / img.height
                        logo_width = 1.2 * inch  # Reduced from 2 inches to 1.2 inches
                        logo_height = logo_width / aspect
                        # Position logo at top right
                        p.drawImage(logo_path, width - logo_width - 20*mm, height - logo_height - 10*mm,
                                  width=logo_width, height=logo_height)
                except Exception as e:
                    print(f"Error loading logo: {e}")
            
            # Company Information (Left side)
            y = height - 30*mm
            p.setFont("Helvetica-Bold", 14)  # Reduced from 16 to 14
            p.drawString(20*mm, y, settings.site_name)
            y -= 6*mm  # Reduced spacing
            
            p.setFont("Helvetica", 9)  # Reduced from 10 to 9
            if settings.contact_address:
                for line in settings.contact_address.split('\n'):
                    p.drawString(20*mm, y, line.strip())
                    y -= 4*mm  # Reduced spacing
            if settings.contact_phone:
                p.drawString(20*mm, y, f"Phone: {settings.contact_phone}")
                y -= 4*mm
            if settings.contact_email:
                p.drawString(20*mm, y, f"Email: {settings.contact_email}")
                y -= 4*mm
            
            # Invoice Information (Right side)
            p.setFont("Helvetica-Bold", 18)  # Reduced from 20 to 18
            p.drawString(width - 60*mm, height - 25*mm, "INVOICE")
            p.setFont("Helvetica", 9)  # Reduced from 10 to 9
            p.drawString(width - 60*mm, height - 30*mm, f"Invoice #: {self.invoice_number}")
            p.drawString(width - 60*mm, height - 34*mm, f"Date: {self.order_date.strftime('%Y-%m-%d')}")
            p.drawString(width - 60*mm, height - 38*mm, f"Status: {self.get_status_display()}")
            
            # Customer Information
            y = height - 55*mm  # Moved up from 70mm
            p.setFont("Helvetica-Bold", 11)  # Reduced from 12 to 11
            p.drawString(20*mm, y, "Bill To:")
            y -= 6*mm  # Reduced spacing
            
            p.setFont("Helvetica", 9)  # Reduced from 10 to 9
            p.drawString(20*mm, y, self.customer_name)
            y -= 4*mm
            p.drawString(20*mm, y, self.shipping_address)
            y -= 4*mm
            if self.customer_phone:
                p.drawString(20*mm, y, f"Phone: {self.customer_phone}")
                y -= 4*mm
            if self.customer_email:
                p.drawString(20*mm, y, f"Email: {self.customer_email}")
                y -= 4*mm
            
            # Table Header
            y -= 8*mm  # Reduced spacing
            p.setFont("Helvetica-Bold", 9)  # Reduced from 10 to 9
            table_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
            
            # Table Content
            for item in self.items.all():
                table_data.append([
                    item.product.name + (" (Pre-order)" if item.is_preorder else ""),
                    str(item.quantity),
                    f"৳{item.unit_price:,.2f}",
                    f"৳{item.get_total_price():,.2f}"
                ])
            
            # Create table with adjusted column widths
            table = Table(table_data, colWidths=[180, 50, 70, 70])  # Adjusted column widths
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),  # Reduced from 10 to 9
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Reduced from 12 to 8
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Reduced from 9 to 8
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Lighter grid lines
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),  # Added padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Added padding
            ]))
            
            # Draw table
            table.wrapOn(p, width - 40*mm, height)
            table.drawOn(p, 20*mm, y - table._height)
            
            # Totals
            y = y - table._height - 15*mm  # Reduced spacing
            p.setFont("Helvetica-Bold", 9)  # Reduced from 10 to 9
            p.drawString(width - 100*mm, y, "Subtotal:")
            p.drawString(width - 20*mm, y, f"৳{self.total_amount - self.shipping_cost:,.2f}")
            y -= 6*mm  # Reduced spacing
            
            p.drawString(width - 100*mm, y, "Shipping:")
            p.drawString(width - 20*mm, y, f"৳{self.shipping_cost:,.2f}")
            y -= 6*mm
            
            if self.discount_amount > 0:
                p.drawString(width - 100*mm, y, f"Discount ({self.discount_percentage}%):")
                p.drawString(width - 20*mm, y, f"-৳{self.discount_amount:,.2f}")
                y -= 6*mm
            
            p.setFont("Helvetica-Bold", 11)  # Reduced from 12 to 11
            p.drawString(width - 100*mm, y, "Total:")
            p.drawString(width - 20*mm, y, f"৳{self.total_amount:,.2f}")
            y -= 6*mm
            
            p.setFont("Helvetica-Bold", 9)  # Reduced from 10 to 9
            p.drawString(width - 100*mm, y, "Payment Status:")
            p.drawString(width - 20*mm, y, self.get_payment_status_display())
            y -= 6*mm
            
            p.drawString(width - 100*mm, y, "Payment Method:")
            p.drawString(width - 20*mm, y, self.get_payment_method_display())
            
            # Payment Summary
            y -= 15*mm  # Reduced spacing
            p.setFont("Helvetica-Bold", 9)  # Reduced from 10 to 9
            p.drawString(20*mm, y, "Payment Summary:")
            y -= 6*mm
            
            p.setFont("Helvetica", 8)  # Reduced from 9 to 8
            p.drawString(20*mm, y, f"Advance Payment: ৳{self.advance_payment:,.2f}")
            y -= 4*mm
            p.drawString(20*mm, y, f"Payment Collected: ৳{self.payment_collected:,.2f}")
            y -= 4*mm
            p.drawString(20*mm, y, f"Payment Due: ৳{self.payment_due:,.2f}")
            
            # Notes
            if self.order_notes:
                y -= 12*mm  # Reduced spacing
                p.setFont("Helvetica-Bold", 9)  # Reduced from 10 to 9
                p.drawString(20*mm, y, "Order Notes:")
                y -= 6*mm
                p.setFont("Helvetica", 8)  # Reduced from 9 to 8
                for line in self.order_notes.split('\n'):
                    p.drawString(20*mm, y, line.strip())
                    y -= 4*mm
            
            # Footer
            p.setFont("Helvetica-Oblique", 7)  # Reduced from 8 to 7
            p.setFillColor(colors.grey)
            footer_text = settings.copyright_text or "Thank you for your business!"
            p.drawString(20*mm, 15*mm, footer_text)
            p.drawString(20*mm, 10*mm, "This is a computer-generated invoice, no signature required.")
            
            # Add social media links if available
            social_links = []
            if settings.facebook_url: social_links.append("Facebook")
            if settings.instagram_url: social_links.append("Instagram")
            if settings.twitter_url: social_links.append("Twitter")
            if settings.youtube_url: social_links.append("YouTube")
            if settings.threads_url: social_links.append("Threads")
            
            if social_links:
                p.drawString(width - 60*mm, 15*mm, "Follow us on: " + ", ".join(social_links))
            
            p.showPage()
            p.save()
            pdf_data = buffer.getvalue()
            buffer.close()

            # Save PDF to model
            pdf_filename = f"invoice_{self.invoice_number}.pdf"
            self.invoice_date = timezone.now()
            self.invoice_generated = True
            self.invoice_file.save(pdf_filename, ContentFile(pdf_data), save=False)

            # Update stock for each item (only if this is a new invoice)
            if not self.invoice_generated:
                for item in self.items.all():
                    if not item.is_preorder:
                        item.product.update_stock(
                            quantity=-item.quantity,
                            movement_type='SALE',
                            reason=f"Invoice #{self.invoice_number}",
                            user=None
                        )
            self.save()
            return self.invoice_file.path

    def get_invoice_download_url(self):
        """Get the URL for downloading the invoice"""
        if self.invoice_file:
            return reverse('download_invoice', args=[self.id])
        return None

    def get_invoice_status_display(self):
        """Get a human-readable invoice status"""
        if self.invoice_generated:
            return f"Generated on {self.invoice_date.strftime('%Y-%m-%d %H:%M')}"
        return "Not Generated"

    def get_payment_method_display(self):
        """Get human-readable payment method"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)

    def get_payment_status_display(self):
        """Get human-readable payment status"""
        return dict(self.PAYMENT_STATUS_CHOICES).get(self.payment_status, self.payment_status)

    def get_status_display(self):
        """Get human-readable order status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def add_payment(self, amount, method, notes=None, user=None):
        """Record a new payment"""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        payment_record = {
            'date': timezone.now().isoformat(),
            'amount': float(amount),
            'method': method,
            'notes': notes,
            'user': str(user) if user else None
        }
        
        # Update payment history
        if not self.payment_history:
            self.payment_history = []
        self.payment_history.append(payment_record)
        
        # Update payment collected
        self.payment_collected += amount
        self.save()
        
        return payment_record

    def get_payment_summary(self):
        """Get a summary of all payments"""
        return {
            'total_amount': self.total_amount,
            'advance_payment': self.advance_payment,
            'payment_collected': self.payment_collected,
            'payment_due': self.payment_due,
            'payment_status': self.get_payment_status_display(),
            'payment_history': self.payment_history
        }

    def get_discount_summary(self):
        """Get a summary of discounts applied"""
        return {
            'subtotal': self.total_amount + self.discount_amount - self.shipping_cost,
            'discount_amount': self.discount_amount,
            'discount_percentage': self.discount_percentage,
            'shipping_cost': self.shipping_cost,
            'total_amount': self.total_amount
        }

    def send_invoice_email(self):
        """Send invoice email to customer"""
        if not self.customer_email:
            print("No customer email provided")
            return False
            
        try:
            # Get site settings for the email template
            site_settings = SiteSettings.get_settings()
            
            # Get the current site domain
            from django.contrib.sites.models import Site
            try:
                current_site = Site.objects.get_current()
                domain = current_site.domain
                protocol = 'https' if not settings.DEBUG else 'http'
            except:
                domain = settings.SITE_DOMAIN
                protocol = 'https'
            
            # Prepare media URL for logo
            logo_url = None
            if site_settings.navbar_logo:
                try:
                    # Use absolute URL for the logo
                    logo_url = f"{protocol}://{domain}{site_settings.navbar_logo.url}"
                    print(f"DEBUG: Logo URL: {logo_url}")  # Debug print
                except Exception as e:
                    print(f"Error getting logo URL: {str(e)}")
            
            # Render the invoice template with absolute URLs
            html_message = render_to_string('order/invoice.html', {
                'order': self,
                'settings': site_settings,
                'logo_url': logo_url,
                'domain': domain,
                'protocol': protocol,
            })
            
            # Debug prints
            print(f"DEBUG: Sending email to: {self.customer_email}")
            print(f"DEBUG: From email: {settings.EMAIL_HOST_USER}")
            print(f"DEBUG: Subject: Invoice #{self.invoice_number} - {site_settings.site_name}")
            print(f"DEBUG: Logo URL: {logo_url}")
            
            # Create email message
            email = EmailMessage(
                subject=f'Invoice #{self.invoice_number} - {site_settings.site_name}',
                body=html_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[self.customer_email],
                headers={'Reply-To': settings.EMAIL_HOST_USER}
            )
            email.content_subtype = "html"  # Main content is now text/html
            
            # Send email
            email.send(fail_silently=False)
            print("DEBUG: Email sent successfully")
            return True
        except Exception as e:
            print(f"Error sending invoice email: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_preorder = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, null=True,
        help_text="Comma-separated tags for this item")
    notes = models.TextField(blank=True, null=True,
        help_text="Additional notes about this item")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order #{self.order.id}"

    def get_total_price(self):
        if self.quantity is None or self.unit_price is None:
            return 0
        return self.quantity * self.unit_price

    def get_tags_list(self):
        """Get list of tags"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]

    def add_tag(self, tag):
        """Add a tag to the item"""
        tags = self.get_tags_list()
        if tag not in tags:
            tags.append(tag)
            self.tags = ', '.join(tags)
            self.save()

    def remove_tag(self, tag):
        """Remove a tag from the item"""
        tags = self.get_tags_list()
        if tag in tags:
            tags.remove(tag)
            self.tags = ', '.join(tags)
            self.save()

    def save(self, *args, **kwargs):
        # Set unit price from product if not set
        if self.unit_price is None or self.unit_price == 0:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
        
        # Update order totals after saving
        if self.order:
            self.order.save()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        # Update order totals after deletion
        if order:
            order.save()

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
        ('ADJUSTMENT', 'Adjustment'),
        ('RETURN', 'Return'),
        ('CANCELLED_ORDER', 'Cancelled Order'),
    ]

    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE, related_name='stock_movements')
    quantity = models.IntegerField()
    type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.product.name} ({self.quantity})"


