import os
import sys
import django
import logging
import json
import time
import requests
import hmac
import hashlib
from django.utils import timezone

# Configure logging to show more details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanjilas.settings')
django.setup()

from shipping.api_client import (
    get_access_token,
    get_cities,
    get_zones_by_city,
    get_areas_by_zone,
    get_merchant_stores,
    calculate_price,
    get_and_store_all_data,
    get_default_store,
    create_order,
    get_order_short_info
)
from shipping.models import PathaoStore, PathaoCredentials, PathaoToken, PathaoOrder

def debug_response(response, step_name):
    """Helper function to debug API responses"""
    logging.debug(f"\n{'='*50}")
    logging.debug(f"DEBUG: {step_name}")
    logging.debug(f"Status Code: {response.status_code}")
    logging.debug(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
    try:
        logging.debug(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except:
        logging.debug(f"Response Text: {response.text}")
    logging.debug(f"{'='*50}\n")

def clear_stored_token():
    """Clear any stored token to force new token generation"""
    PathaoToken.objects.all().delete()
    logging.info("Cleared stored token")

def update_credentials():
    """Update the credentials in the database"""
    logging.info("Updating Pathao credentials...")
    try:
        credentials, created = PathaoCredentials.objects.get_or_create(pk=1)
        credentials.client_id = "q9wdLmwejP"
        credentials.client_secret = "rlC2iyALBeELbxfUS4LpdJAfmoKAqH3bpHNbadjk"
        credentials.default_username = "sanjila901@gmail.com"
        credentials.default_password = "afroafri117!"
        # Add webhook configuration
        credentials.webhook_secret = "egjnlvlyVeqk5lmMIfadFdDqOgZ3tjmdnp5lUIQW4LI"
        credentials.webhook_url = "https://your-domain.com/shipping/api/webhook/pathao/"  # Update this when deploying
        credentials.save()
        logging.info("✅ Credentials updated successfully")
    except Exception as e:
        logging.error(f"❌ Failed to update credentials: {str(e)}")
        return False
    return True

def create_test_order():
    """
    Create a test order using the specified store and phone number
    """
    logging.info("Starting order creation test...")
    
    # First update credentials and clear stored token
    if not update_credentials():
        return
    clear_stored_token()
    
    # Get Access Token
    logging.info("Getting access token...")
    access_token = get_access_token(is_test=False)  # Using production credentials
    if not access_token:
        logging.error("❌ Failed to obtain access token")
        return
    
    # Debug token storage
    try:
        token_obj = PathaoToken.objects.get(pk=1)
        logging.debug(f"\nStored Token Details:")
        logging.debug(f"Access Token: {token_obj.access_token[:20]}...")
        logging.debug(f"Refresh Token: {token_obj.refresh_token[:20] if token_obj.refresh_token else 'None'}...")
        logging.debug(f"Expires At: {token_obj.expires_at}")
    except PathaoToken.DoesNotExist:
        logging.error("❌ No token found in database")
        return
    
    # Get the specific store
    try:
        store = PathaoStore.objects.get(id=594)  # Using the database ID
        logging.info(f"✅ Found store: {store.store_name} (ID: {store.store_id})")
        logging.debug(f"Store Details:")
        logging.debug(f"City ID: {store.city_id}")
        logging.debug(f"Zone ID: {store.zone_id}")
        logging.debug(f"Is Active: {store.is_active}")
        logging.debug(f"Is Default: {store.is_default_store}")
    except PathaoStore.DoesNotExist:
        logging.error("❌ Store not found")
        return
    
    # Create order data
    order_data = {
        'store_id': store.store_id,  # Using Pathao store ID
        'merchant_order_id': f'ORDER_{int(time.time())}',  # Unique order ID
        'recipient_name': 'Test Recipient',
        'recipient_phone': '01911269258',
        'recipient_address': 'Test Address, Test City',
        'recipient_city': store.city_id,  # Using store's city ID
        'recipient_zone': store.zone_id,  # Using store's zone ID
        'recipient_area': 1,  # First area in the zone
        'delivery_type': 48,  # Regular delivery
        'item_type': 2,  # Parcel
        'special_instruction': 'Test delivery instruction',
        'item_quantity': 1,
        'item_weight': 0.5,
        'item_description': 'Test item description',
        'amount_to_collect': 0,
        'item_price': 100,
        'payment_type': 1,
        'recipient_email': 'test@example.com',
        'recipient_landmark': 'Near Test Landmark'
    }
    
    logging.debug(f"\nOrder Data:")
    logging.debug(json.dumps(order_data, indent=2))
    
    # Create the order
    logging.info("\nCreating order...")
    order_response = create_order(order_data, is_test=False)  # Using production API
    if order_response and order_response.get('type') == 'success':
        consignment_id = order_response.get('data', {}).get('consignment_id')
        logging.info("✅ Successfully created order")
        logging.debug(f"Full Order Response:")
        logging.debug(json.dumps(order_response, indent=2))
        
        # Get order status
        logging.info("\nChecking order status...")
        order_info = get_order_short_info(consignment_id, is_test=False)  # Using production API
        if order_info and order_info.get('type') == 'success':
            logging.info("✅ Successfully retrieved order status")
            logging.debug(f"Full Order Status Response:")
            logging.debug(json.dumps(order_info, indent=2))
        else:
            logging.error("❌ Failed to retrieve order status")
            if order_info:
                logging.error(f"Error details: {json.dumps(order_info, indent=2)}")
    else:
        logging.error("❌ Failed to create order")
        if order_response:
            logging.error(f"Error details: {json.dumps(order_response, indent=2)}")

def setup_production_environment():
    """
    Set up the production environment with the specified store
    """
    logging.info("Setting up production environment...")
    
    # Clear any existing default stores
    PathaoStore.objects.filter(is_default_store=True).update(is_default_store=False)
    logging.info("Cleared all default store flags")
    
    # Get all stores
    stores = get_merchant_stores(is_test=False)
    if not stores:
        logging.error("❌ Failed to get merchant stores")
        return
    
    # Find SANJILA's New Shop
    target_store = None
    for store in stores:
        if store.get('store_name') == "SANJILA's New Shop":
            target_store = store
            break
    
    if not target_store:
        logging.error("❌ Could not find SANJILA's New Shop in the store list")
        return
    
    # Update the store in database
    store_obj, created = PathaoStore.objects.get_or_create(
        store_id=target_store.get('store_id'),
        defaults={
            'store_name': target_store.get('store_name'),
            'store_address': target_store.get('store_address'),
            'is_active': True,
            'city_id': target_store.get('city_id'),
            'zone_id': target_store.get('zone_id'),
            'hub_id': target_store.get('hub_id'),
            'is_default_store': True
        }
    )
    
    if not created:
        store_obj.is_default_store = True
        store_obj.save()
    
    logging.info(f"✅ Successfully set up production environment with store: {store_obj.store_name} (ID: {store_obj.store_id})")

def test_webhook_locally():
    """
    Test webhook functionality locally by simulating a webhook request.
    This is for development/testing purposes only.
    """
    # Get credentials
    try:
        credentials = PathaoCredentials.objects.get(pk=1)
        webhook_secret = credentials.webhook_secret
        if not webhook_secret:
            logging.error("❌ No webhook secret configured")
            return False
    except PathaoCredentials.DoesNotExist:
        logging.error("❌ Pathao credentials not found")
        return False
    
    # Get a real consignment ID from the database
    try:
        pathao_order = PathaoOrder.objects.filter(consignment_id__isnull=False).first()
        if not pathao_order:
            logging.error("❌ No Pathao orders found in database")
            return False
        consignment_id = pathao_order.consignment_id
        logging.info(f"Using consignment ID: {consignment_id}")
    except Exception as e:
        logging.error(f"❌ Error getting consignment ID: {str(e)}")
        return False
    
    # Create test webhook payload
    payload = {
        "consignment_id": consignment_id,
        "status": "Delivered",
        "status_slug": "delivered",
        "updated_at": timezone.now().isoformat()
    }
    
    # Generate signature
    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Send test webhook request
    headers = {
        'Content-Type': 'application/json',
        'X-Pathao-Signature': signature
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/shipping/api/webhook/pathao/',
            headers=headers,
            json=payload
        )
        logging.info(f"Webhook test response: {response.status_code}")
        logging.info(f"Response content: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"❌ Failed to test webhook: {str(e)}")
        return False

if __name__ == "__main__":
    # First run the test
    create_test_order()
    
    # Then set up production
    setup_production_environment() 