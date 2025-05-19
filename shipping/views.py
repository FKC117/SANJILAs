from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .api_client import create_order, get_default_store
from order.models import Order
from .models import PathaoCity, PathaoZone, PathaoArea
import logging

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
