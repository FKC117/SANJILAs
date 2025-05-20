from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from shop.models import Product
from django.contrib import messages
from .models import Order, OrderItem, ShippingRate
from shipping.models import PathaoCity, PathaoZone, PathaoArea
import json
from decimal import Decimal  # Add this import at the top
from django.db.models import Q, Case, When, IntegerField
from .models import StockMovement
from django.utils import timezone
from django.db.models import F

def cart_add(request):
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                product_id = data.get('product_id')
                quantity = int(data.get('quantity', 1))
                is_preorder = data.get('is_preorder', False)
            else:
                product_id = request.POST.get('product_id')
                quantity = int(request.POST.get('quantity', 1))
                is_preorder = request.POST.get('is_preorder', False)

            if not product_id:
                return JsonResponse({'success': False, 'message': 'No product ID provided'})
                
            if quantity <= 0:
                return JsonResponse({'success': False, 'message': 'Invalid quantity'})
            
            # Get the product or return an error response if not found
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Product not found'})
                
            # Check stock availability only if not a preorder
            if not is_preorder and product.stock is not None and product.stock < quantity:
                return JsonResponse({
                    'success': False, 
                    'message': f'Only {product.stock} items available in stock'
                })
                
            # Add to cart
            cart = Cart(request)
            cart.add(product, quantity)
            
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_total_quantity(),
                'message': f'{product.name} added to your cart.',
                'is_preorder': is_preorder
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        except Exception as e:
            # Log the error and return a generic error message
            print(f"Error in cart_add: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred while adding the product to cart'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def cart_remove(request):
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                product_id = data.get('product_id')
            else:
                product_id = request.POST.get('product_id')

            if not product_id:
                return JsonResponse({'success': False, 'message': 'No product ID provided'})
            
            # Convert product_id to string since that's what the cart expects
            product_id = str(product_id)
            
            # Get the product or return an error response if not found
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Product not found'})
            
            # Remove from cart
            cart = Cart(request)
            cart.remove(product_id)
            
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_total_quantity(),
                'message': f'{product.name} removed from your cart.'
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        except Exception as e:
            # Log the error and return a generic error message
            print(f"Error in cart_remove: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred while removing the product from cart'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def cart_update(request):
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                product_id = data.get('product_id')
                quantity = int(data.get('quantity', 1))
            else:
                product_id = request.POST.get('product_id')
                quantity = int(request.POST.get('quantity', 1))

            if not product_id:
                return JsonResponse({'success': False, 'message': 'No product ID provided'})
            
            try:
                quantity = int(quantity)
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid quantity value'})
                
            if quantity < 0:
                return JsonResponse({'success': False, 'message': 'Quantity cannot be negative'})
            
            # Get the product or return an error response if not found
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Product not found'})
            
            # Check stock availability
            if quantity > 0 and product.stock is not None and product.stock < quantity:
                return JsonResponse({
                    'success': False, 
                    'message': f'Only {product.stock} items available in stock'
                })
            
            # Update cart
            cart = Cart(request)
            cart.update(product_id, quantity)
            
            # Calculate new subtotal for this item
            item_subtotal = product.get_selling_price() * quantity if quantity > 0 else 0
            
            # Calculate cart totals safely
            cart_total = 0
            for item in cart:
                try:
                    cart_total += item['product'].get_selling_price() * item['quantity']
                except (AttributeError, TypeError):
                    continue
            
            # Get shipping cost based on location
            shipping_location = request.session.get('shipping_location', 'inside_dhaka')
            shipping_cost = ShippingRate.get_rate(shipping_location)
            
            # Calculate grand total
            grand_total = cart_total + shipping_cost
            
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_total_quantity(),
                'cart_total': float(cart_total),
                'item_subtotal': float(item_subtotal),
                'shipping_cost': float(shipping_cost),
                'grand_total': float(grand_total),
                'message': 'Cart updated.'
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        except Exception as e:
            # Log the error and return a generic error message
            print(f"Error in cart_update: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred while updating the cart'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def cart_view(request):
    try:
        cart = Cart(request)
        cart_items = []
        
        # Get user's shipping location from session or default to inside_dhaka
        shipping_location = request.session.get('shipping_location', 'inside_dhaka')
        
        # Process cart items safely
        for item in cart:
            try:
                product = item['product']
                quantity = item['quantity']
                
                # Get prices safely
                price = product.get_selling_price()
                subtotal = price * quantity
                
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except (KeyError, AttributeError, TypeError) as e:
                # Skip items that cause errors
                print(f"Error processing cart item: {e}")
                continue
        
        # Calculate cart totals
        cart_total = 0
        for item in cart_items:
            try:
                cart_total += item['subtotal']
            except (TypeError, KeyError) as e:
                print(f"Error calculating cart item subtotal: {e}")
                continue
        
        # Handle shipping location changes
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                new_shipping_location = request.POST.get('shipping_location')
                if new_shipping_location in ['inside_dhaka', 'outside_dhaka']:
                    shipping_location = new_shipping_location
                    request.session['shipping_location'] = shipping_location
                    request.session.modified = True
                    print(f"Updated shipping location to: {shipping_location}")
            except Exception as e:
                print(f"Error updating shipping location: {e}")
        
        # Get shipping cost based on location
        try:
            shipping_cost = ShippingRate.get_rate(shipping_location)
        except Exception as e:
            print(f"Error getting shipping rate: {e}")
            shipping_cost = 0
        
        discount = 0  # Implement coupon system later
        total = cart_total + shipping_cost - discount
        
        # For AJAX requests, return updated totals
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_total': float(cart_total),
                'shipping_cost': float(shipping_cost),
                'grand_total': float(total),
                'cart_count': cart.get_total_quantity()
            })
        
        # Get shipping rates for display
        try:
            inside_dhaka_rate = ShippingRate.get_rate('inside_dhaka')
            outside_dhaka_rate = ShippingRate.get_rate('outside_dhaka')
        except Exception as e:
            print(f"Error getting shipping rates for display: {e}")
            inside_dhaka_rate = 75  # Default rates as fallback
            outside_dhaka_rate = 125
        
        context = {
            'cart_items': cart_items,
            'cart_total': cart_total,
            'shipping_cost': shipping_cost,
            'discount': discount,
            'total': total,
            'shipping_location': shipping_location,
            'shipping_rates': {
                'inside_dhaka': inside_dhaka_rate,
                'outside_dhaka': outside_dhaka_rate
            },
            'related_products': get_related_products(cart_items)
        }
        
        return render(request, 'shop/cart.html', context)
    
    except Exception as e:
        # Log the error and return a simple error view
        print(f"Error rendering cart view: {e}")
        messages.error(request, "There was an error loading your cart. Please try again.")
        
        # Return a simplified cart view
        return render(request, 'shop/cart.html', {
            'cart_items': [],
            'cart_total': 0,
            'shipping_cost': 0,
            'discount': 0,
            'total': 0,
            'shipping_location': 'inside_dhaka',
            'shipping_rates': {
                'inside_dhaka': 75,
                'outside_dhaka': 125
            },
            'error': True
        })

def checkout_view(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty. Add some products before checkout.')
        return redirect('cart_view')

    shipping_location = request.session.get('shipping_location', 'inside_dhaka')
    print(f"Current shipping location from session: {shipping_location}")

    # AJAX: Handle shipping location changes
    if request.method == 'POST' and 'shipping_location' in request.POST and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("Received shipping location update request")
        print(f"POST data: {request.POST}")
        print(f"Headers: {request.headers}")
        
        new_shipping_location = request.POST.get('shipping_location')
        print(f"New shipping location: {new_shipping_location}")
        
        request.session['shipping_location'] = new_shipping_location
        request.session.modified = True  # Ensure session is saved
        print(f"Updated session shipping location: {request.session.get('shipping_location')}")

        cart_total_price = Decimal(str(cart.get_total_price()))
        print(f"Cart total: {cart_total_price}")
        
        try:
            shipping_cost = Decimal(str(ShippingRate.get_rate(new_shipping_location)))
            print(f"New shipping cost: {shipping_cost}")
        except Exception as e:
            print(f"Error getting shipping rate: {e}")
            shipping_cost = Decimal('0')

        total = cart_total_price + shipping_cost
        print(f"New total: {total}")

        response_data = {
            'success': True,
            'shipping_cost': float(shipping_cost),
            'total': float(total)
        }
        print(f"Sending response: {response_data}")
        return JsonResponse(response_data)

    # AJAX: Handle zone fetch
    if request.method == 'POST' and 'city_id' in request.POST and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            city_id = request.POST.get('city_id')
            zones = PathaoZone.objects.filter(city__city_id=city_id).values('zone_id', 'zone_name')
            return JsonResponse({
                'success': True,
                'zones': list(zones)
            })
        except Exception as e:
            print(f"Error fetching zones: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to fetch zones'
            })

    # AJAX: Handle area fetch
    if request.method == 'POST' and 'zone_id' in request.POST and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            zone_id = request.POST.get('zone_id')
            areas = PathaoArea.objects.filter(zone__zone_id=zone_id).values('area_id', 'area_name')
            return JsonResponse({
                'success': True,
                'areas': list(areas)
            })
        except Exception as e:
            print(f"Error fetching areas: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to fetch areas'
            })

    # POST: Handle order placement
    if request.method == 'POST' and 'customer_name' in request.POST:
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', '')
        shipping_address = request.POST.get('shipping_address')
        city_id = request.POST.get('city')
        zone_id = request.POST.get('zone')
        area_id = request.POST.get('area')
        current_shipping_location = request.POST.get('shipping_location', shipping_location)
        
        # Get city, zone, and area objects from IDs
        try:
            city = PathaoCity.objects.get(city_id=city_id)
            zone = PathaoZone.objects.get(zone_id=zone_id, city=city)
            area = PathaoArea.objects.get(area_id=area_id, zone=zone) if area_id and area_id.strip() else None
        except (PathaoCity.DoesNotExist, PathaoZone.DoesNotExist):
            messages.error(request, 'Invalid city or zone selected.')
            return redirect('checkout')
        except PathaoArea.DoesNotExist:
            messages.error(request, 'Invalid area selected.')
            return redirect('checkout')
        
        # Calculate totals using Decimal
        order_subtotal = Decimal(str(cart.get_total_price()))
        try:
            current_shipping_cost = Decimal(str(ShippingRate.get_rate(current_shipping_location)))
        except Exception as e:
            print(f"Error getting shipping rate for order creation: {e}")
            current_shipping_cost = Decimal('0')

        total_amount = order_subtotal + current_shipping_cost

        order = Order.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            shipping_address=shipping_address,
            city=city.city_id,  # Store ID
            zone=zone.zone_id,  # Store ID
            area=area.area_id if area else None,  # Store ID
            city_name=city.city_name,  # Store name for display
            zone_name=zone.zone_name,  # Store name for display
            area_name=area.area_name if area else None,  # Store name for display
            shipping_location=current_shipping_location,
            shipping_cost=current_shipping_cost,
            total_amount=total_amount,
            status='pending'
        )

        # Create order items
        for item in cart:
            try:
                product_instance = item['product']
                OrderItem.objects.create(
                    order=order,
                    product=product_instance,
                    quantity=item['quantity'],
                    unit_price=Decimal(str(product_instance.get_selling_price())),
                    is_preorder=product_instance.preorder
                )

                # Update stock if not a preorder
                if not product_instance.preorder:
                    # Update product stock
                    product_instance.stock -= item['quantity']
                    if product_instance.stock <= 0:
                        product_instance.stock = 0
                        # Only set available to False if not a preorder product
                        if not product_instance.preorder:
                            product_instance.available = False
                    product_instance.save()

                    # Create stock movement record
                    StockMovement.objects.create(
                        product=product_instance,
                        quantity=-item['quantity'],  # Negative for stock out
                        type='SALE',
                        reason=f'Order #{order.id}'
                    )

                    # Update product analytics
                    from accounts.models import ProductAnalytics
                    try:
                        # Try to get existing analytics record
                        analytics = ProductAnalytics.objects.get(
                            product=product_instance,
                            date=timezone.now().date()
                        )
                        # Update existing record
                        analytics.quantity_sold = F('quantity_sold') + item['quantity']
                        analytics.total_sales = F('total_sales') + (item['quantity'] * Decimal(str(product_instance.get_selling_price())))
                        analytics.total_cost = F('total_cost') + (item['quantity'] * product_instance.buying_price)
                        analytics.stock_level = product_instance.stock
                        analytics.save()
                    except ProductAnalytics.DoesNotExist:
                        # Create new record if it doesn't exist
                        ProductAnalytics.objects.create(
                            product=product_instance,
                            date=timezone.now().date(),
                            quantity_sold=item['quantity'],
                            total_sales=item['quantity'] * Decimal(str(product_instance.get_selling_price())),
                            total_cost=item['quantity'] * product_instance.buying_price,
                            stock_level=product_instance.stock
                        )

            except (KeyError, AttributeError, Exception) as e:
                print(f"Error creating order item for product ID {item.get('product_id', 'N/A')}: {e}")
                continue
        
        # Update daily sales
        from accounts.models import DailySales
        try:
            # Try to get existing daily sales record
            daily_sales = DailySales.objects.get(date=timezone.now().date())
            # Update existing record
            daily_sales.total_sales = F('total_sales') + order.total_amount
            daily_sales.total_orders = F('total_orders') + 1
            daily_sales.total_cost = F('total_cost') + sum(item.quantity * item.product.buying_price for item in order.items.all())
            daily_sales.total_expenses = F('total_expenses') + order.shipping_cost
            daily_sales.save()
        except DailySales.DoesNotExist:
            # Create new record if it doesn't exist
            DailySales.objects.create(
                date=timezone.now().date(),
                total_sales=order.total_amount,
                total_orders=1,
                total_cost=sum(item.quantity * item.product.buying_price for item in order.items.all()),
                total_expenses=order.shipping_cost
            )

        cart.clear()
        messages.success(request, f'Order #{order.id} placed successfully!')
        
        # Store order details in session for Meta Pixel tracking
        request.session['last_order'] = {
            'id': order.id,
            'total_amount': float(total_amount),
            'currency': 'bdt',
            'items': [
                {
                    'id': item.product.id,
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.unit_price)
                } for item in order.items.all()
            ]
        }
        
        return redirect('order_success_generic')

    # GET: Display checkout page
    template_cart_items = []
    for item in cart:
        try:
            product_obj = item['product']
            price = Decimal(str(product_obj.get_selling_price()))
            quantity = item['quantity']
            subtotal = price * Decimal(str(quantity))
            
            template_cart_items.append({
                'product': product_obj,
                'quantity': quantity,
                'subtotal': subtotal,
                'first_image_url': product_obj.first_image,
                'product_name': product_obj.name
            })
        except (KeyError, AttributeError, Exception) as e:
            print(f"Error preparing item for checkout display (product ID {item.get('product_id', 'N/A')}): {e}")
            continue

    current_cart_total = Decimal(str(cart.get_total_price()))
    try:
        current_shipping_cost = Decimal(str(ShippingRate.get_rate(shipping_location)))
    except Exception as e:
        print(f"Error getting shipping rate for checkout display: {e}")
        current_shipping_cost = Decimal('0')

    discount = Decimal('0')  # Placeholder for future coupon system
    grand_total = current_cart_total + current_shipping_cost - discount

    # Get shipping rates for display
    try:
        inside_dhaka_rate = Decimal(str(ShippingRate.get_rate('inside_dhaka')))
        outside_dhaka_rate = Decimal(str(ShippingRate.get_rate('outside_dhaka')))
    except Exception as e:
        print(f"Error getting shipping rates for display options: {e}")
        inside_dhaka_rate = Decimal('75')
        outside_dhaka_rate = Decimal('125')
    
    # Get all cities for the dropdown
    cities = PathaoCity.objects.all().values('city_id', 'city_name')
        
    context = {
        'cart_items': template_cart_items,
        'cart_total': current_cart_total,
        'shipping_cost': current_shipping_cost,
        'discount': discount,
        'total': grand_total,
        'shipping_location': shipping_location,
        'shipping_rates': {
            'inside_dhaka': inside_dhaka_rate,
            'outside_dhaka': outside_dhaka_rate,
        },
        'cities': cities
    }
    return render(request, 'shop/checkout.html', context)

def order_success_generic(request):
    """
    Generic order success page that works with session data and includes Meta Pixel tracking.
    """
    # Get order details from session
    order_data = request.session.get('last_order')
    
    if not order_data:
        # If no order data in session, redirect to home
        messages.warning(request, 'No order information found.')
        return redirect('index')
    
    # Get the actual order from database
    try:
        order = Order.objects.get(id=order_data['id'])
        order_items = OrderItem.objects.filter(order=order)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('index')
    
    context = {
        'order': order,
        'order_items': order_items,
        'meta_pixel_data': {
            'content_type': 'product',
            'content_ids': [str(item['id']) for item in order_data['items']],
            'content_name': [item['name'] for item in order_data['items']],
            'value': order_data['total_amount'],
            'currency': order_data['currency'],
            'num_items': sum(item['quantity'] for item in order_data['items'])
        }
    }
    
    # Clear the order data from session after using it
    if 'last_order' in request.session:
        del request.session['last_order']
    
    return render(request, 'shop/order_success.html', context)

# Keep the old order_success view for backward compatibility
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    # Prepare Meta Pixel data
    meta_pixel_data = {
        'content_type': 'product',
        'content_ids': [str(item.product.id) for item in order_items],
        'content_name': [item.product.name for item in order_items],
        'value': float(order.total_amount),
        'currency': 'bdt',
        'num_items': sum(item.quantity for item in order_items)
    }
    
    context = {
        'order': order,
        'order_items': order_items,
        'meta_pixel_data': meta_pixel_data
    }
    
    return render(request, 'shop/order_success.html', context)

def cart_context_processor(request):
    """
    Context processor to make the cart available in all templates
    """
    try:
        # Create cart instance
        cart = Cart(request)
        
        # Calculate total quantity safely
        try:
            cart_count = cart.get_total_quantity()
        except Exception as e:
            print(f"Error calculating cart count in context processor: {e}")
            cart_count = 0
            
        return {
            'cart': cart,
            'cart_count': cart_count
        }
    except Exception as e:
        # Log the specific error that occurred
        print(f"Error in cart_context_processor: {e}")
        return {
            'cart': None,
            'cart_count': 0
        }

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            # save an empty cart in the session
            cart = self.session['cart'] = {}
        self.cart = cart # self.cart will store dicts like {product_id: {'quantity': Q, 'price': P, 'is_preorder': B}}
    
    @property
    def has_preorder_items(self):
        """
        Check if there are any preorder items in the cart.
        """
        try:
            return any(item.get('is_preorder', False) for item in self.cart.values())
        except Exception as e:
            print(f"Error checking for preorder items: {e}")
            return False
    
    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        Stores product_id, quantity, price (as string), and is_preorder flag in the session.
        """
        try:
            product_id = str(product.id)
            selling_price = str(product.get_selling_price()) # Store price as string
            
            if product_id not in self.cart:
                self.cart[product_id] = {
                    'quantity': 0,
                    'price': selling_price,
                    'is_preorder': product.preorder
                }
            
            if override_quantity:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.cart[product_id]['quantity'] += quantity
            
            # Make sure quantity doesn't exceed available stock only if not a preorder
            if not self.cart[product_id]['is_preorder'] and product.stock is not None and self.cart[product_id]['quantity'] > product.stock:
                self.cart[product_id]['quantity'] = product.stock
            
            # Ensure price is up-to-date in cart if it changed on product
            self.cart[product_id]['price'] = selling_price

            self.save()
        except (AttributeError, ValueError) as e:
            print(f"Error adding product to cart: {e}")
            # Do not re-raise or return, allow graceful failure if product data is bad
            return
    
    def update(self, product_id, quantity):
        """
        Update quantity for specified product.
        Also updates the price in the cart if it has changed on the Product model.
        """
        try:
            product_id = str(product_id)
            if product_id not in self.cart:
                return False # Product not in cart
                
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                # If product doesn't exist anymore, remove it from cart
                if product_id in self.cart:
                    del self.cart[product_id]
                    self.save()
                return False
                
            # Make sure quantity doesn't exceed available stock only if not a preorder
            if not self.cart[product_id]['is_preorder'] and product.stock is not None and quantity > product.stock:
                quantity = product.stock
            
            # Update quantity    
            self.cart[product_id]['quantity'] = quantity
            
            # Update price in cart to reflect current product price
            self.cart[product_id]['price'] = str(product.get_selling_price())
            
            # Remove item if quantity is 0 or less
            if quantity <= 0:
                self.remove(product_id) # remove calls save()
            else:
                self.save()
                
            return True
        except Exception as e:
            print(f"Error updating cart item {product_id}: {e}")
            return False
    
    def remove(self, product_id):
        """
        Remove a product from the cart.
        """
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def save(self):
        # update the session cart
        self.session['cart'] = self.cart
        # mark the session as "modified" to make sure it's saved
        self.session.modified = True
    
    def clear(self):
        # empty cart
        self.session['cart'] = {}
        self.session.modified = True
    
    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        The Product object is added here at runtime and NOT stored in the session.
        """
        product_ids = list(self.cart.keys()) # Get a list of keys to avoid issues if cart changes during iteration
        
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}
        
        # Store items to remove if their product no longer exists
        ids_to_remove_from_cart = []

        for product_id in product_ids:
            if product_id not in product_map:
                # Product associated with this ID no longer exists in DB
                ids_to_remove_from_cart.append(product_id)
                continue

            item_data_from_session = self.cart[product_id]
            # Create a copy of the item data to avoid modifying session directly
            # when adding the non-serializable Product object.
            item_for_iteration = item_data_from_session.copy()
            
            try:
                item_for_iteration['product'] = product_map[product_id]
                # Ensure price is float for calculations, but it was stored as string
                item_for_iteration['price'] = float(item_data_from_session['price'])
                item_for_iteration['total_price'] = item_for_iteration['price'] * item_for_iteration['quantity']
                yield item_for_iteration
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                print(f"Error processing cart item {product_id} during iteration: {e}")
                # Potentially mark for removal if data is corrupt
                ids_to_remove_from_cart.append(product_id)
                continue
        
        # Clean up cart from items whose products were not found or caused errors
        if ids_to_remove_from_cart:
            for product_id_to_remove in set(ids_to_remove_from_cart): # Use set to avoid duplicate removals
                if product_id_to_remove in self.cart:
                    del self.cart[product_id_to_remove]
            self.save() # Save changes to the session cart
    
    def get_total_price(self):
        """
        Calculate the total price of all items in the cart.
        Returns 0 if there are any errors.
        """
        try:
            total = 0
            for item_id, item_data in self.cart.items():
                try:
                    price = float(item_data['price'])
                    quantity = item_data['quantity']
                    total += price * quantity
                except (ValueError, KeyError, TypeError):
                    # Skip items with invalid data
                    continue
            return total
        except Exception as e:
            print(f"Error calculating cart total price: {e}")
            return 0
    
    def get_total_quantity(self):
        """
        Calculate the total quantity of all items in the cart.
        Returns 0 if there are any errors.
        """
        try:
            return sum(item['quantity'] for item in self.cart.values())
        except Exception as e:
            print(f"Error calculating cart total quantity: {e}")
            return 0

    def __len__(self):
        """
        Return the number of unique items in the cart.
        This makes the Cart class support len() operations.
        """
        try:
            return len(self.cart)
        except Exception as e:
            print(f"Error calculating cart length: {e}")
            return 0

def create_order(request):
    if request.method == 'POST':
        try:
            cart = Cart(request)
            if not cart:
                return JsonResponse({'success': False, 'message': 'Cart is empty'})

            # Create the order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                # ... other order fields ...
            )

            # Process each item in the cart
            for product_id, item in cart.cart.items():
                try:
                    product = Product.objects.get(id=product_id)
                    quantity = item['quantity']
                    is_preorder = item.get('is_preorder', False)

                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=Decimal(item['price']),
                        is_preorder=is_preorder
                    )

                    # Update stock if not a preorder
                    if not is_preorder:
                        # Update product stock
                        product.stock -= quantity
                        if product.stock <= 0:
                            product.stock = 0
                            # Only set available to False if not a preorder product
                            if not product.preorder:
                                product.available = False
                        product.save()

                        # Create stock movement record
                        StockMovement.objects.create(
                            product=product,
                            quantity=-quantity,  # Negative for stock out
                            type='SALE',
                            reason=f'Order #{order.id}'
                        )

                except Product.DoesNotExist:
                    # Handle case where product no longer exists
                    continue

            # Clear the cart
            cart.clear()

            return JsonResponse({
                'success': True,
                'message': 'Order created successfully',
                'order_id': order.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating order: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def cancel_order(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            if order.status not in ['pending', 'processing']:
                return JsonResponse({
                    'success': False,
                    'message': 'Only pending or processing orders can be cancelled'
                })

            # Update order status
            order.status = 'cancelled'
            order.save()

            # Return items to stock if they were not preorders
            for item in order.items.all():
                if not item.is_preorder:
                    product = item.product
                    product.stock += item.quantity
                    product.available = True  # Make product available again
                    product.save()

                    # Create stock movement record for return
                    StockMovement.objects.create(
                        product=product,
                        quantity=item.quantity,  # Positive for stock in
                        type='CANCELLED_ORDER',
                        reason=f'Order #{order.id} cancelled'
                    )

                    # Update product analytics
                    from accounts.models import ProductAnalytics
                    try:
                        # Try to get existing analytics record
                        analytics = ProductAnalytics.objects.get(
                            product=product,
                            date=timezone.now().date()
                        )
                        # Update existing record
                        analytics.quantity_sold = F('quantity_sold') - item.quantity
                        analytics.total_sales = F('total_sales') - (item.quantity * item.unit_price)
                        analytics.total_cost = F('total_cost') - (item.quantity * product.buying_price)
                        analytics.stock_level = product.stock
                        analytics.save()
                    except ProductAnalytics.DoesNotExist:
                        # Create new record if it doesn't exist
                        ProductAnalytics.objects.create(
                            product=product,
                            date=timezone.now().date(),
                            quantity_sold=item.quantity,
                            total_sales=item.quantity * item.unit_price,
                            total_cost=item.quantity * product.buying_price,
                            stock_level=product.stock
                        )

            # Update daily sales
            from accounts.models import DailySales
            try:
                # Try to get existing daily sales record
                daily_sales = DailySales.objects.get(date=timezone.now().date())
                # Update existing record
                daily_sales.total_sales = F('total_sales') - order.total_amount
                daily_sales.total_orders = F('total_orders') - 1
                daily_sales.total_cost = F('total_cost') - sum(item.quantity * item.product.buying_price for item in order.items.all())
                daily_sales.total_expenses = F('total_expenses') - order.shipping_cost
                daily_sales.save()
            except DailySales.DoesNotExist:
                # Create new record if it doesn't exist
                DailySales.objects.create(
                    date=timezone.now().date(),
                    total_sales=order.total_amount,
                    total_orders=1,
                    total_cost=sum(item.quantity * item.product.buying_price for item in order.items.all()),
                    total_expenses=order.shipping_cost
                )

            return JsonResponse({
                'success': True,
                'message': 'Order cancelled successfully'
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error cancelling order: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def get_related_products(cart_items):
    """
    Get related products based on cart items' categories and subcategories.
    Returns up to 4 related products.
    """
    try:
        if not cart_items:
            return []
            
        # Get categories and subcategories from cart items
        categories = set()
        subcategories = set()
        for item in cart_items:
            try:
                product = item['product']
                if product.category:
                    categories.add(product.category)
                if product.subcategory:
                    subcategories.add(product.subcategory)
            except (AttributeError, TypeError) as e:
                print(f"Error getting category/subcategory: {e}")
                continue

        # Get products from the same categories and subcategories
        # Prioritize products from the same subcategory first
        related_products = Product.objects.filter(
            Q(subcategory__in=subcategories) | Q(category__in=categories),
            available=True
        ).exclude(
            id__in=[item['product'].id for item in cart_items]
        ).order_by(
            # Order by subcategory match first, then random
            Case(
                When(subcategory__in=subcategories, then=0),
                default=1,
                output_field=IntegerField(),
            ),
            '?'
        )[:4]  # Limit to 4 products
        
        return related_products
    except Exception as e:
        print(f"Error getting related products: {e}")
        return []










