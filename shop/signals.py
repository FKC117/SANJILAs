from django.db.models.signals import post_save
from django.dispatch import receiver
from order.models import Order
from .models import Customer

@receiver(post_save, sender=Order)
def create_or_update_customer(sender, instance, created, **kwargs):
    """
    Signal to automatically create or update customer when an order is created
    """
    if created:  # Only process new orders
        customer, is_new = Customer.get_or_create_from_order(instance)
        # You can add additional logic here if needed, like sending welcome emails for new customers
        if is_new:
            print(f"New customer created: {customer.name} ({customer.phone})")
        else:
            print(f"Existing customer updated: {customer.name} ({customer.phone})") 