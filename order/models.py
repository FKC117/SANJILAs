from django.db import models
from shop.models import Product
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
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
    payment_method = models.CharField(max_length=50, default='cash_on_delivery')
    payment_status = models.CharField(max_length=20, default='pending')
    order_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_preorder = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order #{self.order.id}"

    def get_total_price(self):
        return self.quantity * self.unit_price

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


