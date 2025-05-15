from django.db import models

# Create your models here.
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
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.TextField()
    city = models.CharField(max_length=50, blank=False)
    zone = models.CharField(max_length=50, blank=False)
    area = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return f"Order {self.id} by {self.customer_name} on {self.order_date.strftime('%Y-%m-%d %H:%M:%S')} status is {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_preorder = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order #{self.order.id}"

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
