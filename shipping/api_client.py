import requests
from django.conf import settings
import json
from datetime import datetime, timedelta
import os
import logging
from django.utils import timezone
from django.db import transaction # Import transaction for atomic operations

# Import your new models
from .models import PathaoCredentials, PathaoToken, PathaoCity, PathaoZone, PathaoArea, PathaoStore, PathaoOrder
# Assuming you might need your internal Order model later
# from your_order_app.models import Order as InternalOrder


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_credentials(is_test=True):
    """Retrieves Pathao API credentials from the database."""
    try:
        credentials = PathaoCredentials.objects.get(pk=1)
        logging.debug(f"\nRetrieved Credentials:")
        logging.debug(f"Client ID: {credentials.client_id}")
        logging.debug(f"Username: {credentials.default_username}")
        logging.debug(f"Base URL: {settings.PATHAO_COURIER_PRODUCTION_BASE_URL if not is_test else settings.PATHAO_COURIER_SANDBOX_BASE_URL}")
        
        if is_test:
            return {
                'client_id': credentials.test_client_id or credentials.client_id,
                'client_secret': credentials.test_client_secret or credentials.client_secret,
                'username': credentials.test_username or credentials.default_username,
                'password': credentials.test_password or credentials.default_password,
                'base_url': settings.PATHAO_COURIER_SANDBOX_BASE_URL,
            }
        else:
            return {
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'username': credentials.default_username,
                'password': credentials.default_password,
                'base_url': settings.PATHAO_COURIER_PRODUCTION_BASE_URL,
            }
    except PathaoCredentials.DoesNotExist:
        logging.error("PathaoCredentials object not found in the database. Please add credentials.")
        return None

def _get_stored_token():
    """Retrieves the stored token from the database."""
    try:
        # Assuming only one token object for simplicity, adjust if managing tokens per merchant
        return PathaoToken.objects.get(pk=1)
    except PathaoToken.DoesNotExist:
        logging.info("No PathaoToken found in the database.")
        return None

def _store_token(access_token, refresh_token, expires_in):
    """Stores the new token in the database."""
    # Calculate expiry time, subtracting a small buffer (e.g., 5 minutes)
    expires_at = timezone.now() + timedelta(seconds=expires_in - 300) # 300 seconds = 5 minutes

    # Assuming only one token object, update or create it
    token_obj, created = PathaoToken.objects.get_or_create(
        pk=1, # Use a fixed ID for the single token object
        defaults={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at,
        }
    )
    if not created:
        token_obj.access_token = access_token
        token_obj.refresh_token = refresh_token
        token_obj.expires_at = expires_at
        token_obj.save()
        logging.info("PathaoToken updated in database.")
    else:
        logging.info("PathaoToken created in database.")


def get_access_token(is_test=True):
    """
    Obtains or refreshes the Pathao API access token.
    Uses refresh token if available and not expired, otherwise issues a new token.
    Returns the access token string or None on failure.
    """
    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    token_obj = _get_stored_token()

    if token_obj and not token_obj.is_expired():
        logging.info("Using stored and valid access token.")
        return token_obj.access_token

    issue_token_url = f'{credentials["base_url"]}/aladdin/api/v1/issue-token'

    # Attempt to refresh token if a refresh token exists
    if token_obj and token_obj.refresh_token:
        logging.info("Attempting to refresh token...")
        payload = {
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": token_obj.refresh_token,
        }
        try:
            logging.debug(f"\nRefresh Token Request:")
            logging.debug(f"URL: {issue_token_url}")
            logging.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(issue_token_url, json=payload)
            logging.debug(f"\nRefresh Token Response:")
            logging.debug(f"Status Code: {response.status_code}")
            logging.debug(f"Response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            _store_token(data['access_token'], data['refresh_token'], data['expires_in'])
            logging.info("Token refreshed successfully.")
            return data['access_token']
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to refresh token: {e}.")
        except KeyError as e:
            logging.error(f"Refresh token response missing key: {e}.")

    # If no valid token or refresh failed, issue a new token
    logging.info("Issuing a new access token...")
    payload = {
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
        "grant_type": "password",
        "username": credentials["username"],
        "password": credentials["password"],
    }

    try:
        logging.debug(f"\nNew Token Request:")
        logging.debug(f"URL: {issue_token_url}")
        logging.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(issue_token_url, json=payload)
        logging.debug(f"\nNew Token Response:")
        logging.debug(f"Status Code: {response.status_code}")
        logging.debug(f"Response: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        _store_token(data['access_token'], data['refresh_token'], data['expires_in'])
        logging.info("New token issued successfully.")
        return data['access_token']
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to issue new token: {e}.")
        return None
    except KeyError as e:
        logging.error(f"New token response missing key: {e}.")
        return None

# --- API Call Functions (Updated to use get_access_token) ---

def create_single_order(order_data, is_test=True):
    """
    Creates a single new order in Pathao Courier Merchant API.
    Requires a dictionary containing the order details.
    Returns the API response dictionary on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot create single order.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    create_order_url = f'{credentials["base_url"]}/aladdin/api/v1/orders'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        logging.info(f"Creating single order with data: {order_data}")
        response = requests.post(create_order_url, headers=headers, json=order_data)
        response.raise_for_status() # Raise an exception for bad status codes
        logging.info(f"Single order created successfully. Response: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create single order: {e}. Response: {response.text if response else 'N/A'}")
        return None

def create_bulk_orders(orders_list, is_test=True):
    """
    Creates multiple orders in bulk via Pathao Courier Merchant API.
    Requires a list of dictionaries, where each dictionary is order data.
    Returns the API response dictionary on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot create bulk orders.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    create_bulk_url = f'{credentials["base_url"]}/aladdin/api/v1/orders/bulk'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    payload = {"orders": orders_list}

    try:
        logging.info(f"Creating bulk orders. Number of orders: {len(orders_list)}")
        response = requests.post(create_bulk_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Bulk orders created successfully. Response: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create bulk orders: {e}. Response: {response.text if response else 'N/A'}")
        return None

def get_order_short_info(consignment_id, is_test=True):
    """
    Gets a short summary of a specific order from Pathao Courier Merchant API.
    Requires the consignment_id.
    Returns the API response dictionary on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot get order short info.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    get_info_url = f'{credentials["base_url"]}/aladdin/api/v1/orders/{consignment_id}/info'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    try:
        logging.debug(f"\nGet Order Info Request:")
        logging.debug(f"URL: {get_info_url}")
        logging.debug(f"Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.get(get_info_url, headers=headers)
        logging.debug(f"\nGet Order Info Response:")
        logging.debug(f"Status Code: {response.status_code}")
        logging.debug(f"Response: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get order short info for consignment ID {consignment_id}: {e}.")
        if 'response' in locals() and response is not None:
            logging.error(f"Response: {response.text}")
        return None
    except KeyError as e:
        logging.error(f"Order info response missing key: {e}.")
        return None


def get_cities(is_test=True):
    """
    Gets the list of available cities from Pathao Courier Merchant API.
    Returns a list of city dictionaries on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot get city list.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    city_list_url = f'{credentials["base_url"]}/aladdin/api/v1/city-list'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    try:
        logging.info("Fetching city list.")
        response = requests.get(city_list_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        cities_data = data.get('data', {}).get('data', [])
        logging.info("City list fetched successfully.")
        
        # Store cities in the database
        for city_data in cities_data:
            PathaoCity.objects.get_or_create(
                city_id=city_data.get('city_id'),
                defaults={'city_name': city_data.get('city_name')}
            )
        
        return cities_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get city list: {e}.")
        return None
    except KeyError as e:
        logging.error(f"City list response missing key: {e}.")
        return None


def get_zones_by_city(city_id, is_test=True):
    """
    Gets the list of zones for a given city ID from Pathao Courier Merchant API.
    Returns a list of zone dictionaries on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot get zone list.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    zone_list_url = f'{credentials["base_url"]}/aladdin/api/v1/cities/{city_id}/zone-list'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    try:
        logging.info(f"Fetching zone list for city ID: {city_id}")
        response = requests.get(zone_list_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        zones_data = data.get('data', {}).get('data', [])
        logging.info(f"Zone list fetched successfully for city ID: {city_id}")
        
        # Store zones in the database
        city = PathaoCity.objects.get(city_id=city_id)
        for zone_data in zones_data:
            PathaoZone.objects.get_or_create(
                zone_id=zone_data.get('zone_id'),
                defaults={
                    'zone_name': zone_data.get('zone_name'),
                    'city': city
                }
            )
        
        return zones_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get zone list for city ID {city_id}: {e}.")
        return None
    except KeyError as e:
        logging.error(f"Zone list response missing key: {e}.")
        return None


def get_areas_by_zone(zone_id, is_test=True):
    """
    Gets the list of areas for a given zone ID from Pathao Courier Merchant API.
    Returns a list of area dictionaries on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot get area list.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    area_list_url = f'{credentials["base_url"]}/aladdin/api/v1/zones/{zone_id}/area-list'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    try:
        logging.info(f"Fetching area list for zone ID: {zone_id}")
        response = requests.get(area_list_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        areas_data = data.get('data', {}).get('data', [])
        logging.info(f"Area list fetched successfully for zone ID: {zone_id}")
        
        # Store areas in the database
        zone = PathaoZone.objects.get(zone_id=zone_id)
        for area_data in areas_data:
            PathaoArea.objects.get_or_create(
                area_id=area_data.get('area_id'),
                defaults={
                    'area_name': area_data.get('area_name'),
                    'home_delivery_available': area_data.get('home_delivery_available', False),
                    'pickup_available': area_data.get('pickup_available', False),
                    'zone': zone
                }
            )
        
        return areas_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get area list for zone ID {zone_id}: {e}.")
        return None
    except KeyError as e:
        logging.error(f"Area list response missing key: {e}.")
        return None

def calculate_price(price_data, is_test=True):
    """
    Calculates the price of an order using the Pathao Courier Merchant API.
    Requires a dictionary with price calculation details.
    Returns the price data dictionary on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot calculate price.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    price_calculate_url = f'{credentials["base_url"]}/aladdin/api/v1/merchant/price-plan'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    try:
        logging.info(f"Calculating price with data: {price_data}")
        response = requests.post(price_calculate_url, headers=headers, json=price_data)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Price calculation successful. Response: {response.text}")
        return data.get('data')
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to calculate price: {e}. Response: {response.text if response else 'N/A'}")
        return None
    except KeyError as e:
         logging.error(f"Price calculation response missing key: {e}. Full response: {response.text if response else 'N/A'}")
         return None

def get_merchant_stores(is_test=True):
    """
    Gets the list of merchant stores from Pathao Courier Merchant API.
    Returns a list of store dictionaries on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot get merchant stores.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    stores_list_url = f'{credentials["base_url"]}/aladdin/api/v1/stores'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
    }

    try:
        logging.info("Fetching merchant stores list.")
        response = requests.get(stores_list_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info("Merchant stores list fetched successfully.")
        return data.get('data', {}).get('data', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get merchant stores list: {e}. Response: {response.text if response else 'N/A'}")
        return None
    except KeyError as e:
         logging.error(f"Merchant stores response missing key: {e}. Full response: {response.text if response else 'N/A'}")
         return None

def get_and_store_all_data(is_test=True):
    """
    Fetches and stores all cities, zones, areas, and stores from Pathao API.
    Also sets a default store if none exists.
    """
    logging.info("Starting to fetch and store all Pathao data...")
    
    # 1. Get and store all cities
    logging.info("Fetching all cities...")
    cities = get_cities(is_test=is_test)
    if not cities:
        logging.error("Failed to fetch cities. Aborting.")
        return False
    logging.info(f"Successfully stored {len(cities)} cities.")
    
    # 2. Get and store all zones for each city
    total_zones = 0
    for city in cities:
        city_id = city.get('city_id')
        logging.info(f"Fetching zones for city: {city.get('city_name')} (ID: {city_id})")
        zones = get_zones_by_city(city_id, is_test=is_test)
        if zones:
            total_zones += len(zones)
    logging.info(f"Successfully stored {total_zones} zones across all cities.")
    
    # 3. Get and store all areas for each zone
    total_areas = 0
    for zone in PathaoZone.objects.all():
        zone_id = zone.zone_id
        logging.info(f"Fetching areas for zone: {zone.zone_name} (ID: {zone_id})")
        areas = get_areas_by_zone(zone_id, is_test=is_test)
        if areas:
            total_areas += len(areas)
    logging.info(f"Successfully stored {total_areas} areas across all zones.")
    
    # 4. Get and store all stores
    logging.info("Fetching all merchant stores...")
    stores = get_merchant_stores(is_test=is_test)
    if not stores:
        logging.error("Failed to fetch stores. Aborting.")
        return False
    
    # Store stores in database
    for store_data in stores:
        PathaoStore.objects.get_or_create(
            store_id=store_data.get('store_id'),
            defaults={
                'store_name': store_data.get('store_name'),
                'store_address': store_data.get('store_address'),
                'is_active': store_data.get('is_active', True),
                'city_id': store_data.get('city_id'),
                'zone_id': store_data.get('zone_id'),
                'hub_id': store_data.get('hub_id'),
                'is_default_store': store_data.get('is_default_store', False)
            }
        )
    logging.info(f"Successfully stored {len(stores)} stores.")
    
    # 5. Set a default store if none exists
    if not PathaoStore.objects.filter(is_default_store=True).exists():
        # Get the first active store or create one if none exists
        default_store = PathaoStore.objects.filter(is_active=True).first()
        if default_store:
            default_store.is_default_store = True
            default_store.save()
            logging.info(f"Set default store: {default_store.store_name} (ID: {default_store.store_id})")
        else:
            logging.warning("No active stores found to set as default.")
    
    logging.info("Completed fetching and storing all Pathao data.")
    return True

def get_default_store():
    """
    Returns the default store for order creation.
    """
    try:
        return PathaoStore.objects.get(is_default_store=True)
    except PathaoStore.DoesNotExist:
        logging.error("No default store set. Please set a default store first.")
        return None

def create_order(order_data, is_test=True):
    """
    Creates a new order using the Pathao API.
    Requires a dictionary containing the order details.
    Returns the API response dictionary on success, None on failure.
    """
    access_token = get_access_token(is_test=is_test)
    if not access_token:
        logging.error("Could not obtain access token. Cannot create order.")
        return None

    credentials = _get_credentials(is_test=is_test)
    if not credentials:
        return None

    create_order_url = f'{credentials["base_url"]}/aladdin/api/v1/orders'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        logging.debug(f"\nCreate Order Request:")
        logging.debug(f"URL: {create_order_url}")
        logging.debug(f"Headers: {json.dumps(headers, indent=2)}")
        logging.debug(f"Order Data: {json.dumps(order_data, indent=2)}")
        
        response = requests.post(create_order_url, headers=headers, json=order_data)
        logging.debug(f"\nCreate Order Response:")
        logging.debug(f"Status Code: {response.status_code}")
        logging.debug(f"Response: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # Store order in database
        if data.get('type') == 'success':
            order_info = data.get('data', {})
            # Find the internal store object by Pathao store_id
            try:
                store_obj = PathaoStore.objects.get(store_id=order_data.get('store_id'))
            except PathaoStore.DoesNotExist:
                logging.error(f"No PathaoStore found with store_id={order_data.get('store_id')}")
                store_obj = None
            PathaoOrder.objects.create(
                consignment_id=order_info.get('consignment_id'),
                merchant_order_id=order_data.get('merchant_order_id'),
                store=store_obj,  # Use the actual model instance
                recipient_name=order_data.get('recipient_name'),
                recipient_phone=order_data.get('recipient_phone'),
                recipient_address=order_data.get('recipient_address'),
                recipient_city_id=order_data.get('recipient_city'),
                recipient_zone_id=order_data.get('recipient_zone'),
                recipient_area_id=order_data.get('recipient_area'),
                delivery_type=order_data.get('delivery_type'),
                item_type=order_data.get('item_type'),
                special_instruction=order_data.get('special_instruction'),
                item_quantity=order_data.get('item_quantity'),
                item_weight=order_data.get('item_weight'),
                item_description=order_data.get('item_description'),
                amount_to_collect=order_data.get('amount_to_collect'),
                order_status=order_info.get('order_status', 'Pending'),
                order_status_slug=order_info.get('order_status', 'Pending').lower(),
                calculated_price=order_info.get('delivery_fee')
            )
        
        return data
    except requests.exceptions.RequestException as e:
        error_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pathao_order_errors.log')
        error_content = response.text if 'response' in locals() and response is not None else str(e)
        logging.error(f"Failed to create order: {e}.")
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n---\nOrder Data: {json.dumps(order_data, ensure_ascii=False)}\nError: {str(e)}\nResponse: {error_content}\n---\n")
        return None
    except KeyError as e:
        logging.error(f"Order creation response missing key: {e}.")
        return None

