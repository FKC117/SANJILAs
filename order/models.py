from django.db import models
from shop.models import Product

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
    shipping_address = models.TextField()
    city = models.CharField(max_length=50)
    zone = models.CharField(max_length=50, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
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
    STOCK_MOVEMENT_TYPES = [
        ('RESTOCK', 'Restock'),
        ('SALE', 'Sales'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
        ('PURCHASE_ORDER_IN', 'Purchase Order Received'),
        ('PURCHASE_ORDER_OUT', 'Purchase Order Created'),
        ('PREORDER_RESERVATION', 'Preorder Reservation'),
        ('PREORDER_FULFILLMENT', 'Preorder Fulfilled'),
        ('CANCELLED_ORDER', 'Cancelled Order (Stock Returned)'),
        ('DAMAGED', 'Damaged/Lost Stock'),
        ('INVENTORY_COUNT', 'Inventory Count Adjustment')

    ]
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    type = models.CharField(max_length=50, choices=STOCK_MOVEMENT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True, help_text="Optional details about the stock movement")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} of {self.quantity} for {self.product.name} at {self.created_at}"


