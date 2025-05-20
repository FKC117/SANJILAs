from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .api_client import create_order, get_default_store
from order.models import Order
from .models import PathaoCity, PathaoZone, PathaoArea, PathaoOrder, PathaoCredentials, PathaoOrderEvent
import logging
import hmac
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

# Create your views here.

@staff_member_required
@require_http_methods(["POST"])
def initiate_pathao_order(request, order_id):
    """
    Initiates a Pathao order for a given order ID.
    """
    try:
        # Get the order
        order = get_object_or_404(Order, id=order_id)
        
        # Check if order is pending
        if order.status != 'pending':
            return JsonResponse({
                'message': 'Only pending orders can be initiated with Pathao'
            }, status=400)
        
        # Check if order already has a Pathao order
        if order.pathao_orders.exists():
            return JsonResponse({
                'message': 'This order already has a Pathao order'
            }, status=400)
        
        # Get default store
        store = get_default_store()
        if not store:
            return JsonResponse({
                'message': 'No default Pathao store configured'
            }, status=400)
        
        # Get Pathao city, zone, and area
        try:
            pathao_city = PathaoCity.objects.get(city_id=order.city)
            pathao_zone = PathaoZone.objects.get(zone_id=order.zone, city=pathao_city)
            pathao_area = PathaoArea.objects.get(area_id=order.area, zone=pathao_zone) if order.area else None
        except (PathaoCity.DoesNotExist, PathaoZone.DoesNotExist, PathaoArea.DoesNotExist) as e:
            return JsonResponse({
                'message': f'Could not find matching Pathao location: {str(e)}'
            }, status=400)
        
        # Prepare order data for Pathao
        order_data = {
            'store_id': store.store_id,
            'merchant_order_id': f'ORDER_{order.id}',
            'recipient_name': order.customer_name,
            'recipient_phone': order.customer_phone,
            'recipient_address': order.shipping_address,
            'recipient_city': pathao_city.city_id,
            'recipient_zone': pathao_zone.zone_id,
            'recipient_area': pathao_area.area_id,
            'delivery_type': 48,  # Regular delivery
            'item_type': 2,  # Parcel
            'special_instruction': order.order_notes or '',
            'item_quantity': sum(item.quantity for item in order.items.all()),
            'item_weight': 0.5,  # Default weight, adjust as needed
            'item_description': ', '.join([f"{item.product.name} x {item.quantity}" for item in order.items.all()]),
            'amount_to_collect': float(order.total_amount),
            'item_price': float(order.total_amount),
            'payment_type': 1,  # Cash on delivery
        }
        
        # Create Pathao order
        response = create_order(order_data, is_test=False, order_instance=order)
        
        if response and response.get('type') == 'success':
            return JsonResponse({
                'message': 'Pathao order initiated successfully',
                'consignment_id': response.get('data', {}).get('consignment_id')
            })
        else:
            error_message = response.get('message', 'Failed to create Pathao order') if response else 'Failed to create Pathao order'
            return JsonResponse({
                'message': error_message
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error initiating Pathao order: {str(e)}")
        return JsonResponse({
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@staff_member_required
def reinitiate_pathao_order(request, order_id):
    """
    Re-initiates a Pathao order by deleting the existing one and creating a new one.
    Only staff members can access this view.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Check if order is pending
        if order.status != 'pending':
            return JsonResponse({
                'error': 'Only pending orders can be re-initiated'
            }, status=400)
        
        # Get the existing Pathao order
        try:
            existing_pathao_order = order.pathao_orders.first()
            if not existing_pathao_order:
                return JsonResponse({
                    'error': 'No existing Pathao order found'
                }, status=400)
        except Exception as e:
            logging.error(f"Error finding existing Pathao order: {str(e)}")
            return JsonResponse({
                'error': 'Error finding existing Pathao order'
            }, status=500)
        
        # Get the default store
        store = get_default_store()
        if not store:
            return JsonResponse({
                'error': 'No default store configured'
            }, status=400)
        
        # Prepare order data
        order_data = {
            'store_id': store.store_id,
            'merchant_order_id': str(order.id),
            'recipient_name': order.customer_name,
            'recipient_phone': order.customer_phone,
            'recipient_address': order.shipping_address,
            'recipient_city': order.city,
            'recipient_zone': order.zone,
            'recipient_area': order.area,
            'delivery_type': 48,  # Regular delivery
            'item_type': 2,  # Parcel
            'special_instruction': '',
            'item_quantity': 1,
            'item_weight': 0.5,  # Default weight
            'item_description': f'Order #{order.id}',
            'amount_to_collect': float(order.total_amount),
            'payment_type': 1  # Cash on delivery
        }
        
        # Delete the existing Pathao order
        try:
            existing_pathao_order.delete()
            logging.info(f"Deleted existing Pathao order for order {order.id}")
        except Exception as e:
            logging.error(f"Error deleting existing Pathao order: {str(e)}")
            return JsonResponse({
                'error': 'Error deleting existing Pathao order'
            }, status=500)
        
        # Create new Pathao order
        try:
            response = create_order(order_data, is_test=True, order_instance=order)
            if response and response.get('type') == 'success':
                return JsonResponse({
                    'message': 'Pathao order re-initiated successfully'
                })
            else:
                error_message = response.get('message', 'Unknown error') if response else 'No response from Pathao API'
                logging.error(f"Failed to create new Pathao order: {error_message}")
                return JsonResponse({
                    'error': f'Failed to create new Pathao order: {error_message}'
                }, status=500)
        except Exception as e:
            logging.error(f"Error creating new Pathao order: {str(e)}")
            return JsonResponse({
                'error': f'Error creating new Pathao order: {str(e)}'
            }, status=500)
            
    except Order.DoesNotExist:
        return JsonResponse({
            'error': 'Order not found'
        }, status=404)
    except Exception as e:
        logging.error(f"Unexpected error in reinitiate_pathao_order: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred'
        }, status=500)

@csrf_exempt
def pathao_webhook(request):
    """
    Handle Pathao webhook events.
    Requirements:
    1. Return 202 status code
    2. Include X-Pathao-Merchant-Webhook-Integration-Secret header
    3. Handle all event types
    4. Verify webhook signature
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Get webhook secret from credentials
    try:
        credentials = PathaoCredentials.objects.get(pk=1)
        webhook_secret = credentials.webhook_secret
        if not webhook_secret:
            logging.error("No webhook secret configured")
            return JsonResponse({'error': 'Webhook not configured'}, status=500)
    except PathaoCredentials.DoesNotExist:
        logging.error("Pathao credentials not found")
        return JsonResponse({'error': 'Webhook not configured'}, status=500)

    # Verify signature
    signature = request.headers.get('X-PATHAO-Signature')
    if not signature:
        logging.error("No signature in webhook request")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Verify payload signature
    payload = request.body
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        logging.error("Invalid webhook signature")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    try:
        data = json.loads(payload)
        event = data.get('event')
        consignment_id = data.get('consignment_id')
        merchant_order_id = data.get('merchant_order_id')
        updated_at = data.get('updated_at')
        store_id = data.get('store_id')
        delivery_fee = data.get('delivery_fee')

        logging.info(f"Received webhook event: {event}")
        logging.debug(f"Webhook payload: {json.dumps(data, indent=2)}")

        # Handle different event types
        if event == 'webhook_integration':
            # Initial webhook integration test
            response = JsonResponse({'status': 'success'}, status=202)
            response['X-Pathao-Merchant-Webhook-Integration-Secret'] = 'f3992ecc-59da-4cbe-a049-a13da2018d51'
            return response

        # Find the order
        try:
            pathao_order = PathaoOrder.objects.get(consignment_id=consignment_id)
        except PathaoOrder.DoesNotExist:
            logging.error(f"Order not found for consignment ID: {consignment_id}")
            return JsonResponse({'error': 'Order not found'}, status=404)

        # Store the event
        PathaoOrderEvent.objects.create(
            pathao_order=pathao_order,
            event_type=event,
            event_data=data
        )

        # Handle payment invoice event
        if event == 'payment.invoice' and delivery_fee:
            try:
                from accounts.models import Receivable
                from shop.models import Customer
                
                # Get or create Pathao as a customer
                pathao_customer, _ = Customer.objects.get_or_create(
                    name='Pathao',
                    defaults={
                        'contact_person': 'Pathao Support',
                        'phone': '09678-111111',
                        'email': 'support@pathao.com'
                    }
                )
                
                # Create receivable record for the order amount
                main_order = pathao_order.order
                if main_order:
                    Receivable.objects.create(
                        customer=pathao_customer,
                        invoice_number=f"PATH-{consignment_id}",
                        date=timezone.now().date(),
                        due_date=timezone.now().date() + timezone.timedelta(days=30),
                        amount=main_order.total_amount,  # Full order amount
                        status='PENDING',
                        notes=f"Order {consignment_id} - Pathao COD collection"
                    )
                    
                    # Create another receivable for delivery fee (if we're paying it)
                    if delivery_fee:
                        Receivable.objects.create(
                            customer=pathao_customer,
                            invoice_number=f"PATH-DEL-{consignment_id}",
                            date=timezone.now().date(),
                            due_date=timezone.now().date() + timezone.timedelta(days=30),
                            amount=Decimal(str(delivery_fee)),
                            status='PENDING',
                            notes=f"Delivery fee for order {consignment_id}"
                        )
                    
                    logging.info(f"Created receivable records for Pathao order {consignment_id}")
            except Exception as e:
                logging.error(f"Error creating receivable records: {str(e)}")

        # Update order status based on event
        status_mapping = {
            'order.created': 'pending',
            'order.updated': 'processing',
            'pickup.requested': 'processing',
            'pickup.assigned': 'processing',
            'pickup.completed': 'processing',
            'pickup.failed': 'failed',
            'pickup.cancelled': 'cancelled',
            'sorting.hub': 'processing',
            'in.transit': 'processing',
            'last.mile.hub': 'processing',
            'delivery.assigned': 'processing',
            'delivery.completed': 'delivered',
            'delivery.partial': 'partial',
            'return.requested': 'returned',
            'delivery.failed': 'failed',
            'order.on_hold': 'on_hold',
            'payment.invoice': 'processing',
            'return.paid': 'returned',
            'exchange.requested': 'exchange'
        }

        new_status = status_mapping.get(event)
        if new_status:
            pathao_order.order_status = new_status
            pathao_order.order_status_slug = new_status
            pathao_order.pathao_updated_at = timezone.now()
            pathao_order.save()

            # Update main order status if needed
            if new_status in ['delivered', 'cancelled', 'returned']:
                main_order = pathao_order.order
                if main_order:
                    main_order.status = new_status
                    main_order.save()

        # Return success response with required headers
        response = JsonResponse({'status': 'success'}, status=202)
        response['X-Pathao-Merchant-Webhook-Integration-Secret'] = 'f3992ecc-59da-4cbe-a049-a13da2018d51'
        return response

    except json.JSONDecodeError:
        logging.error("Invalid JSON payload")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
