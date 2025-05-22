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
13. [Sales Data Views](#sales-data-views)
14. [Pathao Integration](#pathao-integration)

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

### 3. Invoice System

#### Invoice Generation and Management
The system provides a comprehensive invoice generation and management system with both HTML and PDF capabilities.

##### HTML Invoice Features
- **Standalone HTML Template**: 
  - Complete, self-contained HTML document
  - No template inheritance required
  - Responsive design with print optimization
  - Clean, professional layout

- **Invoice Components**:
  - Company branding with logo
  - Invoice header with company details
  - Customer billing information
  - Itemized product list
  - Payment and shipping details
  - Order notes
  - Social media links
  - Copyright information

- **Styling Features**:
  - Professional grid-based layout
  - Consistent typography
  - Responsive design
  - Print-friendly CSS
  - Centered text alignment for better readability
  - Proper spacing and margins
  - Currency formatting with BDT symbol (৳)

- **Print Optimization**:
  - Print-specific CSS rules
  - Hidden print button when printing
  - Proper page margins
  - Background colors and images preserved
  - Clean table borders

##### Invoice Access and Management
- **URL Access**:
  - Direct URL access: `/order/invoice/<order_id>/`
  - Admin interface integration
  - View and download options

- **Admin Interface Features**:
  - Invoice status indicator
  - Download button
  - View button
  - Bulk invoice generation
  - Invoice regeneration capability

##### Invoice Data
- **Order Information**:
  - Invoice number
  - Order date
  - Order status
  - Payment status
  - Shipping details

- **Product Details**:
  - Product name
  - Quantity
  - Unit price
  - Total price
  - Pre-order indicators

- **Financial Information**:
  - Subtotal
  - Shipping cost
  - Discount (if applicable)
  - Total amount
  - Payment summary
  - Advance payment
  - Payment collected
  - Payment due

##### Implementation Details
```python
# View Implementation
@staff_member_required
def view_invoice(request, order_id):
    """
    View invoice for a specific order:
    1. Retrieve order and site settings
    2. Render invoice template
    3. Handle access control
    """
    order = get_object_or_404(Order, id=order_id)
    settings = SiteSettings.get_settings()
    return render(request, 'order/invoice.html', {
        'order': order,
        'settings': settings
    })
```

##### Template Structure
```html
<!-- Key Template Sections -->
<div class="invoice-container">
    <!-- Header Section -->
    <div class="invoice-header">
        <!-- Company Info -->
        <!-- Logo -->
        <!-- Invoice Info -->
    </div>

    <!-- Customer Details -->
    <div class="invoice-details">
        <!-- Billing Info -->
        <!-- Payment Info -->
    </div>

    <!-- Product Table -->
    <table class="invoice-table">
        <!-- Product List -->
    </table>

    <!-- Totals Section -->
    <div class="totals">
        <!-- Financial Summary -->
    </div>

    <!-- Payment Summary -->
    <div class="payment-summary">
        <!-- Payment Details -->
    </div>

    <!-- Footer -->
    <div class="footer">
        <!-- Copyright -->
        <!-- Social Links -->
    </div>
</div>
```

##### CSS Features
```css
/* Key Style Components */
.invoice-container {
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    background: white;
}

.invoice-header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 20px;
}

.invoice-table {
    width: 100%;
    border-collapse: collapse;
}

/* Print Styles */
@media print {
    .print-button-container {
        display: none;
    }
    
    .invoice-container {
        box-shadow: none;
        border: none;
    }
}
```

##### Security Considerations
- Staff member access required
- Proper data sanitization
- Secure file handling
- Access control for invoice generation
- Protection against unauthorized access

##### Future Enhancements
1. PDF generation with improved styling
2. Email invoice delivery
3. Invoice customization options
4. Bulk invoice operations
5. Invoice archiving system

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

## [UPDATED] Stock Management System

- **All stock movement tracking is now handled by the `StockMovement` model in the `order` app (`SANJILAs/order/models.py`).**
- The `shop` app no longer contains a `StockMovement` model; all references and logic have been consolidated to the `order` app.
- The `Product` model in the `shop` app uses the `related_name='stock_movements'` to access all stock changes via the `order` app's model.
- All staff/admin stock management views, forms, and templates should reference `order.models.StockMovement`.
- Order processing, manual stock adjustments, returns, and cancellations are all tracked in this single model for consistency and auditability.

### Codebase Index (update)
- `SANJILAs/order/models.py`: Contains the single source of truth for stock movements (`StockMovement`).
- `SANJILAs/shop/models.py`: Product model references stock movements via the `order` app.

### Detailed Implementation Guide (update)
- **StockMovement Model**: Now only in `order/models.py`. Tracks all stock changes, including sales, returns, adjustments, and cancellations. Linked to `Product` via a ForeignKey with `related_name='stock_movements'`.
- **Product Model**: Methods like `update_stock` and `get_stock_movements` now use the `order` app's model.

### Business Logic and Implementation Details (update)
- All business logic for stock changes, including order fulfillment, manual adjustments, and returns, is now centralized in the `order` app's `StockMovement` model. This ensures a single audit trail and simplifies reporting and debugging.

## Sales Data Views

### get_sales_data View
- **Purpose**: Retrieves sales data with date filtering
- **Access**: Superuser only
- **Date Handling**:
  - Uses timezone-aware datetime comparisons
  - Converts input dates to timezone-aware datetimes using `timezone.make_aware()`
  - Handles both date range and days-based filtering
- **Data Processing**:
  - Calculates sales breakdown by order status
  - Computes daily sales totals
  - Includes expense calculations
  - Provides profit analysis
- **Response Format**:
  ```json
  {
    "status": "success",
    "data": {
      "daily_data": [
        {
          "date": "YYYY-MM-DD",
          "sales": float,
          "orders": integer
        }
      ],
      "summary": {
        "total_sales": float,
        "total_orders": integer,
        "total_cost": float,
        "gross_profit": float,
        "net_profit": float,
        "total_expenses": float,
        "expenses": {
          "salary": float,
          "advertisement": float,
          "shipping": float,
          "other": float
        },
        "status_breakdown": {
          "delivered": {
            "sales": float,
            "orders": integer,
            "percentage": float
          },
          "shipped": {...},
          "pending": {...}
        }
      }
    }
  }
  ```

### get_product_performance View
- **Purpose**: Retrieves product performance data with date filtering
- **Access**: Superuser only
- **Date Handling**:
  - Uses timezone-aware datetime comparisons
  - Handles both date range and days-based filtering
- **Data Processing**:
  - Calculates product-specific analytics
  - Computes sales, quantity, and cost metrics
  - Includes profit calculations
- **Response Format**:
  ```json
  {
    "status": "success",
    "data": {
      "products": [
        {
          "name": string,
          "category": string,
          "total_sales": float,
          "total_quantity": integer,
          "total_cost": float,
          "avg_daily_sales": float,
          "avg_daily_quantity": float,
          "profit": float
        }
      ],
      "summary": {
        "total_sales": float,
        "total_quantity": integer,
        "total_cost": float,
        "gross_profit": float,
        "net_profit": float,
        "total_expenses": float,
        "expenses": {
          "salary": float,
          "advertisement": float,
          "shipping": float,
          "other": float
        }
      }
    }
  }
  ```

### Date Range Helper Functions

#### get_date_range
- **Purpose**: Helper function to get date range from request parameters
- **Parameters**:
  - `from_date` and `to_date`: Optional date parameters in YYYY-MM-DD format
  - `days`: Optional parameter for number of days to look back
- **Default Behavior**: Returns last 30 days if no valid dates provided
- **Returns**: Tuple of (start_date, end_date) as timezone-aware datetime objects

#### get_daily_summary
- **Purpose**: Get summary of daily financial data
- **Parameters**: Single date
- **Returns**: Dictionary with daily totals for sales, orders, profits, and expenses

#### get_monthly_summary
- **Purpose**: Get summary of monthly financial data
- **Parameters**: Year and month
- **Returns**: Dictionary with monthly totals and profit margin

#### get_period_summary
- **Purpose**: Get summary of financial data for a date range
- **Parameters**: Start and end dates
- **Returns**: Dictionary with period totals for sales, orders, profits, and expenses

### Timezone Handling
- All date comparisons use timezone-aware datetime objects
- Input dates are converted to timezone-aware datetimes using `timezone.make_aware()`
- Date ranges are properly handled with start of day (00:00:00) and end of day (23:59:59)
- Ensures consistent date handling across different timezones

### Error Handling
- Comprehensive error handling with detailed logging
- Returns appropriate error messages with status codes
- Includes error type and traceback information for debugging
- Validates date formats and parameters
- Handles missing or invalid data gracefully

## Pathao Integration

### API Integration
- Uses Pathao's Merchant API for order creation and management
- Supports both test and production environments
- Handles location data (cities, zones, areas)
- Manages store information and credentials

### Token Management
- **Token Storage**: Uses `PathaoToken` model to store access and refresh tokens
- **Token Expiration**: 
  - Access tokens expire after 1 hour
  - System maintains a 5-minute buffer before expiration
  - Expiration time stored in `expires_at` field
- **Token Refresh**:
  - Automatic refresh using refresh token
  - Falls back to new token generation if refresh fails
  - Handled by `get_access_token()` function
- **Token Security**:
  - Tokens stored securely in database
  - Access token used for API requests
  - Refresh token used for token renewal

### Webhook Integration
- **Webhook Configuration**:
  - Webhook secret stored in `PathaoCredentials` model
  - Webhook URL configurable for different environments
  - Supports both test and production webhooks
- **Webhook Security**:
  - Uses HMAC-SHA256 for signature verification
  - Verifies webhook authenticity using stored secret
  - Requires HTTPS in production
- **Webhook Requirements**:
  1. URL must be reachable
  2. URL must resolve within 3 redirections
  3. SSL certificate must be valid (for HTTPS)
  4. Response must be within timeout
  5. Must return 202 status code
  6. Must include `X-Pathao-Merchant-Webhook-Integration-Secret` header
  7. Header value must be `f3992ecc-59da-4cbe-a049-a13da2018d51`

- **Webhook Events**:
  Pathao sends webhook notifications for the following events:

  1. **Order Events**:
     - `order.created`: New order created
     - `order.updated`: Order information updated
     - `order.on_hold`: Order placed on hold

  2. **Pickup Events**:
     - `pickup.requested`: Pickup requested
     - `pickup.assigned`: Assigned for pickup
     - `pickup.completed`: Pickup completed
     - `pickup.failed`: Pickup failed
     - `pickup.cancelled`: Pickup cancelled

  3. **Transit Events**:
     - `sorting.hub`: Package at sorting hub
     - `in.transit`: Package in transit
     - `last.mile.hub`: Received at last mile hub

  4. **Delivery Events**:
     - `delivery.assigned`: Assigned for delivery
     - `delivery.completed`: Successfully delivered
     - `delivery.partial`: Partially delivered
     - `delivery.failed`: Delivery failed

  5. **Return Events**:
     - `return.requested`: Return requested
     - `return.paid`: Return payment received

  6. **Payment Events**:
     - `payment.invoice`: Payment invoice generated

  7. **Exchange Events**:
     - `exchange.requested`: Exchange requested

  Each event updates the order status in our system:
  ```python
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
  ```

  **Event Flow**:
  ```
  Order Created
      ↓
  Pickup Requested → Assigned For Pickup → Pickup
      ↓
  At the Sorting Hub → In Transit → Last Mile Hub
      ↓
  Assigned for Delivery → Delivered
      ↓
  (Optional) Return/Exchange
  ```

  **Status Updates**:
  - Each event updates the `PathaoOrder` status
  - Critical events (delivered, cancelled, returned) also update the main `Order` status
  - All status changes are logged with timestamps
  - Status history is maintained for tracking

  **Event Handling**:
  ```python
  # Example event payload
  {
      "consignment_id": "DL121224VS8TTJ",
      "merchant_order_id": "TS-123",
      "updated_at": "2024-12-27 23:49:43",
      "timestamp": "2024-12-27T17:49:43+00:00",
      "store_id": 130820,
      "event": "delivery.completed",
      "delivery_fee": 83.46
  }

  # System response
  {
      "status": "success"
  }
  Status Code: 202
  Headers: X-Pathao-Merchant-Webhook-Integration-Secret: f3992ecc-59da-4cbe-a049-a13da2018d51
  ```

- **Webhook Response Codes**:
  - 202: Success (with required headers)
  - 400: Invalid signature or payload
  - 404: Order not found
  - 405: Method not allowed
  - 500: Server error

- **Webhook Testing**:
  ```bash
  # Start Django server
  python manage.py runserver

  # In another terminal, test webhook
  python manage.py shell -c "from shipping.test_pathao import test_webhook_locally; test_webhook_locally()"
  ```
  Expected Test Output:
  ```
  INFO - Using consignment ID: DS190525X3B8JH
  DEBUG - Starting new HTTP connection (1): localhost:8000
  DEBUG - http://localhost:8000 "POST /shipping/api/webhook/pathao/ HTTP/1.1" 202 21
  INFO - Webhook test response: 202
  INFO - Response content: {"status": "success"}
  ```

- **Production Setup**:
  1. Update webhook URL in database to production domain
  2. Configure same webhook secret in Pathao dashboard
  3. Enable HTTPS on production server
  4. Test webhook with real orders
  5. Verify all required headers and status codes

- **Error Handling**:
  - Comprehensive error logging
  - Graceful fallback mechanisms
  - Proper exception handling
  - Detailed error messages

- **Security Considerations**:
  - Secure token storage
  - Webhook signature verification
  - HTTPS requirement in production
  - No sensitive data in logs

### Event Tracking System
The system now includes comprehensive event tracking for all Pathao webhook events:

1. **PathaoOrderEvent Model**:
   ```python
   class PathaoOrderEvent(models.Model):
       pathao_order = models.ForeignKey(PathaoOrder, related_name='events')
       event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
       event_data = models.JSONField(help_text="Raw event data from webhook")
       created_at = models.DateTimeField(auto_now_add=True)
   ```

2. **Event Types**:
   - Order Events: created, updated, on hold
   - Pickup Events: requested, assigned, completed, failed, cancelled
   - Transit Events: sorting hub, in transit, last mile hub
   - Delivery Events: assigned, completed, partial, failed
   - Return Events: requested, paid
   - Payment Events: invoice
   - Exchange Events: requested

3. **Event History Access**:
   ```python
   # Get all events for an order
   events = pathao_order.events.all()

   # Get specific event types
   pickup_events = pathao_order.events.filter(event_type='pickup.requested')

   # Get latest event
   latest_event = pathao_order.events.first()
   ```

4. **Status Updates**:
   - Each event updates the `PathaoOrder` status
   - Critical events update the main `Order` status
   - Status history is maintained through events
   - All status changes are timestamped

5. **Event Data Storage**:
   - Raw webhook data is stored in `event_data` JSONField
   - Event type is stored in standardized format
   - Events are ordered by creation time
   - Full event history is maintained

6. **Usage Examples**:
   ```python
   # Track order progress
   order_events = pathao_order.events.all()
   for event in order_events:
       print(f"{event.created_at}: {event.event_type}")

   # Get delivery status
   delivery_events = pathao_order.events.filter(
       event_type__in=['delivery.assigned', 'delivery.completed']
   )

   # Check for issues
   failed_events = pathao_order.events.filter(
       event_type__in=['pickup.failed', 'delivery.failed']
   )
   ```

7. **Admin Interface**:
   - Events are visible in the Django admin
   - Events are linked to their respective orders
   - Full event data is accessible
   - Events can be filtered and searched

8. **Event Flow**:
   ```
   Order Created
       ↓
   Pickup Requested → Assigned For Pickup → Pickup
       ↓
   At the Sorting Hub → In Transit → Last Mile Hub
       ↓
   Assigned for Delivery → Delivered
       ↓
   (Optional) Return/Exchange
   ```

9. **Status Mapping**:
   ```python
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
   ```

10. **Webhook Response**:
    ```json
    {
        "status": "success"
    }
    Status Code: 202
    Headers: X-Pathao-Merchant-Webhook-Integration-Secret: f3992ecc-59da-4cbe-a049-a13da2018d51
    ```