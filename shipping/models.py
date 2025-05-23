from django.db import models
from django.utils import timezone
from datetime import timedelta
from order.models import Order
from django.urls import reverse

class PathaoCredentials(models.Model):
    """
    Stores Pathao API credentials securely.
    Only one instance of this model should exist.
    """
    client_id = models.CharField(max_length=255, help_text="Pathao API Client ID")
    client_secret = models.CharField(max_length=255, help_text="Pathao API Client Secret")
    default_username = models.CharField(max_length=255, blank=True, null=True, help_text="Default username for token issuance")
    default_password = models.CharField(max_length=255, blank=True, null=True, help_text="Default password for token issuance")
    test_client_id = models.CharField(max_length=255, blank=True, null=True, help_text="Pathao Test API Client ID")
    test_client_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Pathao Test API Client Secret")
    test_username = models.CharField(max_length=255, blank=True, null=True, help_text="Test username for token issuance")
    test_password = models.CharField(max_length=255, blank=True, null=True, help_text="Test password for token issuance")
    webhook_url = models.CharField(max_length=255, blank=True, null=True, help_text="Webhook URL for Pathao")
    webhook_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Secret key for verifying webhook signatures")

    class Meta:
        verbose_name_plural = "Pathao Credentials"

    def __str__(self):
        return "Pathao API Credentials"

class PathaoToken(models.Model):
    """
    Stores the current active Pathao API access and refresh tokens.
    Only one instance of this model should exist per set of credentials/merchant.
    """
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When the access token expires (timezone aware)")

    class Meta:
        verbose_name_plural = "Pathao Tokens"

    def is_expired(self):
        """Checks if the token has expired, with a small buffer."""
        return timezone.now() >= self.expires_at - timedelta(minutes=5)

    def __str__(self):
        return f"Pathao Token expiring at {timezone.localtime(self.expires_at).strftime('%Y-%m-%d %H:%M:%S')}"

class PathaoStore(models.Model):
    """
    Stores information about merchant's Pathao stores.
    """
    store_id = models.IntegerField(unique=True, help_text="Unique ID of the Pathao store")
    store_name = models.CharField(max_length=255)
    store_address = models.TextField()
    is_active = models.BooleanField(default=True)
    city_id = models.IntegerField()
    zone_id = models.IntegerField()
    hub_id = models.IntegerField(null=True, blank=True)
    is_default_store = models.BooleanField(default=False, help_text="Set as the default store for placing orders")

    class Meta:
        verbose_name_plural = "Pathao Stores"

    def __str__(self):
        return f"{self.store_name} (ID: {self.store_id})"

    def get_absolute_url(self):
        return reverse('store_detail', kwargs={'store_id': self.store_id})

class PathaoCity(models.Model):
    """
    Stores the list of cities available for Pathao delivery.
    """
    city_id = models.IntegerField(unique=True, help_text="Unique ID of the Pathao city")
    city_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Pathao Cities"

    def __str__(self):
        return self.city_name

    def get_absolute_url(self):
        return reverse('city_detail', kwargs={'city_id': self.city_id})

class PathaoZone(models.Model):
    """
    Stores the list of zones within a Pathao city.
    """
    zone_id = models.IntegerField(unique=True, help_text="Unique ID of the Pathao zone")
    zone_name = models.CharField(max_length=255)
    city = models.ForeignKey(PathaoCity, on_delete=models.CASCADE, related_name='zones')

    class Meta:
        verbose_name_plural = "Pathao Zones"

    def __str__(self):
        return f"{self.zone_name} ({self.city.city_name})"

    def get_absolute_url(self):
        return reverse('zone_detail', kwargs={'zone_id': self.zone_id})

class PathaoArea(models.Model):
    """
    Stores the list of areas within a Pathao zone.
    """
    area_id = models.IntegerField(unique=True, help_text="Unique ID of the Pathao area")
    area_name = models.CharField(max_length=255)
    home_delivery_available = models.BooleanField(default=False)
    pickup_available = models.BooleanField(default=False)
    zone = models.ForeignKey(PathaoZone, on_delete=models.CASCADE, related_name='areas')

    class Meta:
        verbose_name_plural = "Pathao Areas"

    def __str__(self):
        return f"{self.area_name} ({self.zone.zone_name})"

    def get_absolute_url(self):
        return reverse('area_detail', kwargs={'area_id': self.area_id})

class PathaoOrder(models.Model):
    """
    Stores details of orders placed through Pathao Courier.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='pathao_orders', null=True, blank=True)
    consignment_id = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="Unique ID from Pathao for the consignment")
    merchant_order_id = models.CharField(max_length=100, help_text="Your internal order ID sent to Pathao")
    store = models.ForeignKey(PathaoStore, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    recipient_address = models.TextField()
    recipient_city = models.ForeignKey(PathaoCity, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_zone = models.ForeignKey(PathaoZone, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_area = models.ForeignKey(PathaoArea, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_type = models.IntegerField()
    item_type = models.IntegerField()
    special_instruction = models.TextField(blank=True, null=True)
    item_quantity = models.IntegerField(default=1)
    item_weight = models.DecimalField(max_digits=5, decimal_places=2)
    item_description = models.TextField(blank=True, null=True)
    amount_to_collect = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_plan_id = models.IntegerField(null=True, blank=True)
    cod_enabled = models.BooleanField(default=False)
    cod_percentage = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    additional_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order_status = models.CharField(max_length=50, default='Pending')
    order_status_slug = models.CharField(max_length=50, default='Pending', help_text="Slugified status from Pathao")
    pathao_updated_at = models.DateTimeField(null=True, blank=True, help_text="Last updated time from Pathao API")
    invoice_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Pathao Orders"

    def __str__(self):
        return f"Pathao Order: {self.consignment_id or self.merchant_order_id}"

    def get_absolute_url(self):
        return reverse('track_order', kwargs={'consignment_id': self.consignment_id})

class PathaoOrderEvent(models.Model):
    """
    Tracks all webhook events for a Pathao order.
    """
    EVENT_TYPES = [
        ('order.created', 'Order Created'),
        ('order.updated', 'Order Updated'),
        ('pickup.requested', 'Pickup Requested'),
        ('pickup.assigned', 'Assigned For Pickup'),
        ('pickup.completed', 'Pickup Completed'),
        ('pickup.failed', 'Pickup Failed'),
        ('pickup.cancelled', 'Pickup Cancelled'),
        ('sorting.hub', 'At the Sorting Hub'),
        ('in.transit', 'In Transit'),
        ('last.mile.hub', 'Received at Last Mile Hub'),
        ('delivery.assigned', 'Assigned for Delivery'),
        ('delivery.completed', 'Delivered'),
        ('delivery.partial', 'Partial Delivery'),
        ('return.requested', 'Return'),
        ('delivery.failed', 'Delivery Failed'),
        ('order.on_hold', 'On Hold'),
        ('payment.invoice', 'Payment Invoice'),
        ('return.paid', 'Paid Return'),
        ('exchange.requested', 'Exchange')
    ]

    pathao_order = models.ForeignKey(PathaoOrder, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_data = models.JSONField(help_text="Raw event data from webhook")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Pathao Order Events"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pathao_order.consignment_id} - {self.event_type} at {self.created_at}"
