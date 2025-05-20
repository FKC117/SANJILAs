# SANJILA'S E-commerce Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Directory Structure](#directory-structure)
4. [Core Components](#core-components)
5. [Key Features](#key-features)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Frontend Implementation](#frontend-implementation)
9. [Security Considerations](#security-considerations)
10. [Development Guidelines](#development-guidelines)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

## Project Overview
SANJILA'S is a Django-based e-commerce platform specializing in fashion retail. The project implements a full-featured online shopping experience with product management, shopping cart functionality, order processing, and delivery integration.

### Key Technologies
- Backend: Django 4.2.7
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Database: SQLite (Development), PostgreSQL (Production)
- Payment Integration: SSL Commerz
- Delivery Integration: Pathao API
- Additional Tools: Meta Pixel for analytics

## System Architecture

### Backend Architecture
The project follows Django's MVT (Model-View-Template) architecture:
- Models: Data structure definitions in `models.py`
- Views: Business logic in `views.py`
- Templates: HTML templates in `templates/` directory
- URLs: URL routing in `urls.py`

### Frontend Architecture
- Responsive design using Bootstrap 5
- Custom CSS for styling
- JavaScript for dynamic interactions
- AJAX for asynchronous operations

## Directory Structure

```
SANJILAs/
├── accounts/           # User authentication and management
├── shop/              # Product and category management
├── order/             # Order processing and management
├── shipping/          # Delivery and shipping management
├── templates/         # HTML templates
│   ├── base.html      # Base template
│   ├── shop/          # Shop-related templates
│   ├── accounts/      # Authentication templates
│   └── order/         # Order-related templates
├── static/            # Static files (CSS, JS, images)
├── media/             # User-uploaded files
└── sanjilas/          # Project settings and configuration
```

## Codebase Index

### Core Application Files
```
SANJILAs/
├── accounts/
│   ├── models.py          # User and Profile models
│   ├── views.py           # Authentication views
│   ├── forms.py           # User registration and profile forms
│   └── urls.py            # Authentication URLs
│
├── shop/
│   ├── models.py          # Product and Category models
│   ├── views.py           # Product listing and detail views
│   ├── admin.py           # Admin interface customization
│   └── urls.py            # Shop URLs
│
├── order/
│   ├── models.py          # Order and OrderItem models
│   ├── views.py           # Order processing views
│   ├── cart.py            # Cart implementation
│   └── urls.py            # Order URLs
│
├── shipping/
│   ├── models.py          # Zone and Area models
│   ├── views.py           # Shipping calculation views
│   ├── pathao.py          # Pathao API integration
│   └── urls.py            # Shipping URLs
│
└── sanjilas/
    ├── settings.py        # Project settings
    ├── urls.py            # Main URL configuration
    └── wsgi.py           # WSGI configuration
```

### Key Template Files
```
SANJILAs/templates/
├── base.html              # Base template with common elements
├── shop/
│   ├── cart.html          # Shopping cart interface
│   ├── checkout.html      # Checkout process
│   ├── product_list.html  # Product listing page
│   └── product_detail.html # Product detail page
├── accounts/
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   └── profile.html       # User profile page
└── order/
    ├── order_success.html # Order confirmation page
    └── order_detail.html  # Order details page
```

### Static Files
```
SANJILAs/static/
├── css/
│   ├── style.css          # Main stylesheet
│   └── custom.css         # Custom styles
├── js/
│   ├── cart.js            # Cart functionality
│   ├── checkout.js        # Checkout process
│   └── main.js            # Common JavaScript
└── images/                # Static images
```

### Important Configuration Files
```
SANJILAs/
├── requirements.txt       # Project dependencies
├── manage.py             # Django management script
└── pathao_order_errors.log # Delivery error logs
```

### Key Features by File
1. **Cart System**
   - `order/cart.py`: Core cart functionality
   - `order/views.py`: Cart operations (add/update/remove)
   - `templates/shop/cart.html`: Cart interface
   - `static/js/cart.js`: Cart AJAX operations

2. **Order Processing**
   - `order/models.py`: Order data structure
   - `order/views.py`: Order creation and management
   - `templates/order/checkout.html`: Checkout interface
   - `static/js/checkout.js`: Checkout process

3. **Product Management**
   - `shop/models.py`: Product data structure
   - `shop/views.py`: Product listing and details
   - `templates/shop/product_list.html`: Product catalog
   - `templates/shop/product_detail.html`: Product details

4. **User Management**
   - `accounts/models.py`: User and profile models
   - `accounts/views.py`: Authentication and profile management
   - `templates/accounts/login.html`: Login interface
   - `templates/accounts/register.html`: Registration interface

5. **Shipping System**
   - `shipping/models.py`: Zone and area models
   - `shipping/pathao.py`: Delivery integration
   - `shipping/views.py`: Shipping calculations
   - `templates/shop/checkout.html`: Shipping selection

## Detailed Implementation Guide

### Models Documentation

#### 1. Shop App Models (`shop/models.py`)
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    # Used for product categorization and navigation

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_preorder = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Core product information and inventory management

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    # Handles product image management
```

#### 2. Order App Models (`order/models.py`)
```python
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    payment_status = models.CharField(max_length=20)
    # Manages order information and status tracking

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # Tracks individual items in an order
```

#### 3. Accounts App Models (`accounts/models.py`)
```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    # Extends user model with additional information
```

#### 4. Shipping App Models (`shipping/models.py`)
```python
class Zone(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    # Defines delivery zones

class Area(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    # Manages delivery areas and shipping costs
```

### Views Documentation

#### 1. Shop App Views (`shop/views.py`)
```python
# Product Listing
def product_list(request):
    """Displays all active products with filtering and pagination"""
    # Handles product listing, category filtering, and search

def product_detail(request, slug):
    """Shows detailed product information"""
    # Displays product details, related products, and handles cart addition

# Admin Views
@staff_member_required
def product_create(request):
    """Admin view for creating new products"""
    # Handles product creation with image upload

@staff_member_required
def product_update(request, slug):
    """Admin view for updating product information"""
    # Manages product updates and stock management
```

#### 2. Order App Views (`order/views.py`)
```python
# Cart Operations
@require_POST
def cart_add(request):
    """
    Add item to cart with validation:
    1. Validate product exists
    2. Check stock availability
    3. Validate quantity
    4. Add to cart
    5. Return updated cart data
    """
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate product
        product = get_object_or_404(Product, id=product_id)
        
        # Stock validation
        if not product.is_preorder and product.stock < quantity:
            return JsonResponse({
                'status': 'error',
                'message': 'Insufficient stock'
            })
        
        # Add to cart
        cart = Cart(request)
        cart.add(product, quantity)
        
        return JsonResponse({
            'status': 'success',
            'cart_count': cart.get_total_quantity(),
            'cart_total': cart.get_total_price()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def cart_update(request):
    """Updates cart item quantity"""
    # Manages quantity updates with stock checking

def cart_remove(request):
    """Removes item from cart"""
    # Handles cart item removal

# Order Processing
def checkout(request):
    """Handles the checkout process"""
    # Manages order creation, payment, and shipping

def order_success(request):
    """Displays order confirmation"""
    # Shows order details and confirmation
```

#### 3. Accounts App Views (`accounts/views.py`)
```python
def register(request):
    """Handles user registration"""
    # Manages user registration with email verification

def profile(request):
    """Displays and updates user profile"""
    # Handles profile viewing and updating

def order_history(request):
    """Shows user's order history"""
    # Displays past orders with details
```

#### 4. Shipping App Views (`shipping/views.py`)
```python
def calculate_shipping(request):
    """Calculates shipping cost based on area"""
    # Handles shipping cost calculations

def update_shipping_location(request):
    """Updates shipping location in cart"""
    # Manages shipping location updates
```

### URL Patterns Documentation

#### 1. Main URLs (`sanjilas/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('accounts/', include('accounts.urls')),
    path('order/', include('order.urls')),
    path('shipping/', include('shipping.urls')),
]
```

#### 2. Shop URLs (`shop/urls.py`)
```python
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('search/', views.product_search, name='product_search'),
]
```

#### 3. Order URLs (`order/urls.py`)
```python
urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/', views.order_success, name='order_success'),
]
```

#### 4. Accounts URLs (`accounts/urls.py`)
```python
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.order_history, name='order_history'),
]
```

#### 5. Shipping URLs (`shipping/urls.py`)
```python
urlpatterns = [
    path('calculate/', views.calculate_shipping, name='calculate_shipping'),
    path('update-location/', views.update_shipping_location, name='update_shipping_location'),
    path('zones/', views.zone_list, name='zone_list'),
]
```

### Important Notes
1. **Model Relationships**:
   - Products belong to Categories (Many-to-One)
   - Orders have multiple OrderItems (One-to-Many)
   - Users have one Profile (One-to-One)
   - Areas belong to Zones (Many-to-One)

2. **View Security**:
   - Admin views are protected with `@staff_member_required`
   - User-specific views use `@login_required`
   - CSRF protection is enabled for all POST requests

3. **URL Naming**:
   - All URLs have named patterns for reverse lookup
   - Follows RESTful naming conventions
   - Includes versioning for API endpoints

4. **Data Validation**:
   - Models include field validation
   - Views implement form validation
   - Custom validators for specific fields

## Business Logic and Implementation Details

### 1. Shopping Cart System

#### Cart Implementation (`order/cart.py`)
```python
class Cart:
    """
    Session-based shopping cart implementation.
    Uses Django's session framework to store cart data.
    """
    
    def __init__(self, request):
        """
        Initialize cart from session or create new cart.
        Cart data structure:
        {
            'items': {
                'product_id': {
                    'quantity': int,
                    'price': Decimal,
                    'name': str,
                    'image': str
                }
            },
            'shipping_location': {
                'zone_id': int,
                'area_id': int,
                'cost': Decimal
            }
        }
        """
        self.session = request.session
        self.cart = self.session.get('cart', {})
        if 'items' not in self.cart:
            self.cart['items'] = {}
    
    def add(self, product, quantity=1, update_quantity=False):
        """
        Add product to cart with validation:
        1. Check product availability
        2. Validate quantity
        3. Update or add new item
        4. Recalculate totals
        """
        product_id = str(product.id)
        if product_id not in self.cart['items']:
            self.cart['items'][product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name,
                'image': product.first_image.image.url if product.first_image else None
            }
        
        if update_quantity:
            self.cart['items'][product_id]['quantity'] = quantity
        else:
            self.cart['items'][product_id]['quantity'] += quantity
            
        self.save()
    
    def update_shipping(self, zone_id, area_id, cost):
        """
        Update shipping location and cost:
        1. Validate zone and area
        2. Update shipping cost
        3. Recalculate cart total
        """
        self.cart['shipping_location'] = {
            'zone_id': zone_id,
            'area_id': area_id,
            'cost': str(cost)
        }
        self.save()
    
    def get_total_price(self):
        """
        Calculate total price including:
        1. Product subtotal
        2. Shipping cost
        3. Apply any discounts
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart['items'].values()
        ) + Decimal(self.cart.get('shipping_location', {}).get('cost', 0))
```

#### Cart Views Implementation (`order/views.py`)
```python
@require_POST
def cart_add(request):
    """
    Add item to cart with validation:
    1. Validate product exists
    2. Check stock availability
    3. Validate quantity
    4. Add to cart
    5. Return updated cart data
    """
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate product
        product = get_object_or_404(Product, id=product_id)
        
        # Stock validation
        if not product.is_preorder and product.stock < quantity:
            return JsonResponse({
                'status': 'error',
                'message': 'Insufficient stock'
            })
        
        # Add to cart
        cart = Cart(request)
        cart.add(product, quantity)
        
        return JsonResponse({
            'status': 'success',
            'cart_count': cart.get_total_quantity(),
            'cart_total': cart.get_total_price()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
```

##### Example: Add to Cart (Frontend AJAX)
```js
$('#add-to-cart-btn').on('click', function() {
    $.post('/order/cart/add/', {
        product_id: $('#product-id').val(),
        quantity: $('#quantity').val(),
        csrfmiddlewaretoken: '{{ csrf_token }}'
    }, function(response) {
        if (response.status === 'success') {
            updateCartUI(response.cart_count, response.cart_total);
        } else {
            alert(response.message);
        }
    });
});
```

##### Example: API Request/Response
```
POST /order/cart/add/
{
  "product_id": 12,
  "quantity": 2
}

Response:
{
  "status": "success",
  "cart_count": 3,
  "cart_total": 1500.00
}
```

##### Cart Add/Update Process Flow
```
User clicks "Add to Cart"
        |
        v
AJAX POST to /order/cart/add/
        |
        v
[Backend]
- Validate product & stock
- Add/update cart in session
- Return updated cart info
        |
        v
[Frontend]
- Update cart icon/summary
- Show success/error message
```

---

### 2. Order Processing System

#### Order Creation Logic (`order/views.py`)
```python
@login_required
def checkout(request):
    """
    Process checkout with steps:
    1. Validate cart
    2. Process payment
    3. Create order
    4. Update inventory
    5. Send notifications
    """
    cart = Cart(request)
    
    if not cart.cart['items']:
        return redirect('cart_view')
    
    if request.method == 'POST':
        try:
            # 1. Validate shipping information
            shipping_data = validate_shipping(request.POST)
            
            # 2. Process payment
            payment = process_payment(request, cart.get_total_price())
            
            # 3. Create order
            order = Order.objects.create(
                customer=request.user,
                total_amount=cart.get_total_price(),
                shipping_address=shipping_data['address'],
                payment_status=payment.status
            )
            
            # 4. Create order items
            for item in cart.cart['items'].values():
                OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price']
                )
                
                # Update inventory
                product = Product.objects.get(id=item['product_id'])
                if not product.is_preorder:
                    product.stock -= item['quantity']
                    product.save()
            
            # 5. Clear cart and send notifications
            cart.clear()
            send_order_confirmation(order)
            
            return redirect('order_success')
            
        except ValidationError as e:
            return render(request, 'checkout.html', {'error': str(e)})
```

##### Example: Checkout (Frontend AJAX)
```js
$('#checkout-form').on('submit', function(e) {
    e.preventDefault();
    $.post('/order/checkout/', $(this).serialize(), function(response) {
        if (response.status === 'success') {
            window.location.href = response.redirect_url;
        } else {
            $('#checkout-error').text(response.message);
        }
    });
});
```

##### Example: API Request/Response
```
POST /order/checkout/
{
  "shipping_address": "123 Main St",
  "payment_method": "sslcommerz"
}

Response:
{
  "status": "success",
  "redirect_url": "/order/success/"
}
```

##### Checkout & Order Creation Flow
```
User clicks "Checkout"
        |
        v
Validate Cart (stock, shipping, user)
        |
        v
Display Checkout Form
        |
        v
User submits form
        |
        v
[Backend]
- Validate form data
- Process payment (SSLCommerz)
- If payment success:
    - Create Order
    - Deduct stock
    - Send notifications
    - Clear cart
    - Redirect to Success
- If payment fail:
    - Show error
```

---

### 3. Shipping System

#### Shipping Calculation (`shipping/views.py`)
```python
def calculate_shipping(request):
    """
    Calculate shipping cost with rules:
    1. Base cost per zone
    2. Additional cost for remote areas
    3. Free shipping for orders above threshold
    4. Special rates for preorders
    """
    try:
        area_id = request.POST.get('area_id')
        cart_total = Decimal(request.POST.get('cart_total', 0))
        
        area = Area.objects.get(id=area_id)
        base_cost = area.shipping_cost
        
        # Free shipping for orders above threshold
        if cart_total >= settings.FREE_SHIPPING_THRESHOLD:
            return JsonResponse({
                'status': 'success',
                'cost': 0,
                'message': 'Free shipping applied'
            })
        
        # Special handling for preorders
        if request.session.get('cart', {}).get('has_preorder'):
            base_cost *= Decimal('1.2')  # 20% extra for preorders
        
        return JsonResponse({
            'status': 'success',
            'cost': base_cost
        })
    except Area.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid shipping area'
        })
```

##### Example: Shipping Cost Calculation (Frontend AJAX)
```js
$('#shipping-area').on('change', function() {
    $.post('/shipping/calculate/', {
        area_id: $(this).val(),
        cart_total: getCartTotal(),
        csrfmiddlewaretoken: '{{ csrf_token }}'
    }, function(response) {
        if (response.status === 'success') {
            $('#shipping-cost').text(response.cost);
        }
    });
});
```

##### Example: API Request/Response
```
POST /shipping/calculate/
{
  "area_id": 5,
  "cart_total": 2000.00
}

Response:
{
  "status": "success",
  "cost": 100.00
}
```

##### Shipping Calculation Flow
```
User selects shipping area
        |
        v
AJAX POST to /shipping/calculate/
        |
        v
[Backend]
- Lookup area & base cost
- Apply free shipping/preorder rules
- Return shipping cost
        |
        v
[Frontend]
- Update shipping cost in summary
```

---

### 4. Payment Processing

#### SSL Commerz Integration (`order/payment.py`)
```python
class SSLCommerzPayment:
    """
    SSL Commerz payment integration:
    1. Generate payment session
    2. Handle payment validation
    3. Process payment response
    4. Update order status
    """
    
    def create_payment_session(self, order):
        """
        Create payment session with:
        1. Order details
        2. Customer information
        3. Shipping details
        4. Success/fail URLs
        """
        data = {
            'store_id': settings.SSL_STORE_ID,
            'store_passwd': settings.SSL_STORE_PASSWORD,
            'total_amount': order.total_amount,
            'currency': 'BDT',
            'tran_id': f'ORDER_{order.id}',
            'product_category': 'Fashion',
            'success_url': reverse('payment_success'),
            'fail_url': reverse('payment_fail'),
            'cancel_url': reverse('payment_cancel'),
            'cus_name': order.customer.get_full_name(),
            'cus_email': order.customer.email,
            'cus_phone': order.customer.profile.phone,
            'cus_add1': order.shipping_address,
            'shipping_method': 'NO',
            'product_name': 'SANJILA\'S Order',
            'product_profile': 'general'
        }
        
        return self._make_api_request('create', data)
    
    def validate_payment(self, response_data):
        """
        Validate payment response:
        1. Verify transaction ID
        2. Check amount
        3. Validate status
        4. Update order
        """
        if not self._verify_hash(response_data):
            raise PaymentValidationError('Invalid payment response')
            
        if response_data['status'] == 'VALID':
            order = Order.objects.get(
                id=response_data['tran_id'].split('_')[1]
            )
            order.payment_status = 'completed'
            order.save()
            return True
            
        return False
```

##### Example: Payment Session Creation (Backend)
```python
payment = SSLCommerzPayment()
session = payment.create_payment_session(order)
# Redirect user to session['GatewayPageURL']
```

##### Example: Payment Validation (Backend)
```python
def payment_callback(request):
    response_data = request.POST
    payment = SSLCommerzPayment()
    if payment.validate_payment(response_data):
        # Payment successful, update order
        ...
    else:
        # Payment failed, show error
        ...
```

##### Payment Flow
```
User submits order with payment
        |
        v
Create payment session (SSLCommerz)
        |
        v
User redirected to payment gateway
        |
        v
User completes payment
        |
        v
Payment gateway calls callback URL
        |
        v
[Backend]
- Validate payment
- Update order status
- Notify user
```

---

### 5. User Registration

#### User Registration (`accounts/views.py`)
```python
def register(request):
    """
    User registration with steps:
    1. Validate form data
    2. Check email uniqueness
    3. Create user and profile
    4. Send verification email
    5. Handle phone verification
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Create profile
                Profile.objects.create(
                    user=user,
                    phone=form.cleaned_data['phone'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city']
                )
                
                # Send verification email
                send_verification_email(user)
                
                # Handle phone verification
                send_verification_sms(user.profile.phone)
                
                return redirect('login')
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})
```

##### Example: Registration (Frontend AJAX)
```js
$('#register-form').on('submit', function(e) {
    e.preventDefault();
    $.post('/accounts/register/', $(this).serialize(), function(response) {
        if (response.status === 'success') {
            window.location.href = '/accounts/login/';
        } else {
            $('#register-error').text(response.message);
        }
    });
});
```

##### Example: API Request/Response
```
POST /accounts/register/
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secret123",
  "phone": "01712345678"
}

Response:
{
  "status": "success",
  "redirect_url": "/accounts/login/"
}
```

##### Registration Flow
```
User fills registration form
        |
        v
AJAX POST to /accounts/register/
        |
        v
[Backend]
- Validate form data
- Create user & profile
- Send verification email/SMS
- Return success or error
        |
        v
[Frontend]
- Redirect to login or show error
```

---

## Core Components

### 1. Product Management (`shop/`)
- Product CRUD operations
- Category management
- Image handling
- Stock management
- Pre-order system

Key Files:
- `models.py`: Product, Category, ProductImage models
- `views.py`: Product listing, detail, search views
- `admin.py`: Admin interface customization

### 2. Shopping Cart (`order/`)
- Session-based cart implementation
- Cart operations (add, update, remove)
- Price calculations
- Stock validation

Key Files:
- `cart.py`: Cart class implementation
- `views.py`: Cart operation views
- `templates/shop/cart.html`: Cart interface

### 3. Order Processing (`order/`)
- Order creation and management
- Payment processing
- Order status tracking
- Delivery integration

Key Files:
- `models.py`: Order, OrderItem models
- `views.py`: Order processing views
- `templates/order/checkout.html`: Checkout interface

### 4. User Management (`accounts/`)
- User registration and authentication
- Profile management
- Address management
- Order history

Key Files:
- `models.py`: User, Profile models
- `views.py`: Authentication views
- `forms.py`: User forms

### 5. Shipping Management (`shipping/`)
- Delivery zone management
- Shipping cost calculation
- Pathao integration
- Delivery tracking

Key Files:
- `models.py`: Zone, Area models
- `views.py`: Shipping calculation views
- `pathao.py`: Pathao API integration

## Key Features

### 1. Shopping Cart System
- Real-time cart updates
- Quantity validation
- Stock checking
- Price calculations
- Shipping cost integration

Important Considerations:
- Cart data is session-based
- Stock validation on every operation
- Price calculations include shipping
- Cart updates use AJAX for smooth UX

### 2. Order Processing
- Multi-step checkout
- Address validation
- Payment integration
- Order confirmation
- Email notifications

Important Considerations:
- Order status transitions
- Payment verification
- Stock deduction
- Delivery assignment

### 3. Product Management
- Product categorization
- Image handling
- Stock management
- Pre-order system
- Price management

Important Considerations:
- Image optimization
- Stock synchronization
- Pre-order handling
- Price formatting

### 4. User System
- Registration and login
- Profile management
- Address management
- Order history
- Password reset

Important Considerations:
- Email verification
- Password security
- Session management
- Profile updates

## Database Schema

### Key Models

1. Product
```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_preorder = models.BooleanField(default=False)
    # ... other fields
```

2. Order
```python
class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    # ... other fields
```

3. Cart
```python
class Cart:
    def __init__(self, request):
        self.session = request.session
        # ... implementation
```

## API Endpoints

### Cart Operations
- `POST /cart/add/`: Add item to cart
- `POST /cart/update/`: Update cart item quantity
- `POST /cart/remove/`: Remove item from cart
- `GET /cart/view/`: View cart contents

### Order Operations
- `POST /order/create/`: Create new order
- `GET /order/status/<order_id>/`: Check order status
- `POST /order/cancel/<order_id>/`: Cancel order

### Product Operations
- `GET /products/`: List all products
- `GET /products/<id>/`: Get product details