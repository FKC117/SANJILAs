from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    # Staff authentication URLs
    path('staff/login/', auth_views.LoginView.as_view(
        template_name='shop/staff/login.html',
        redirect_authenticated_user=True,
        next_page=None  # Let the view handle next parameter
    ), name='staff_login'),
    path('staff/logout/', auth_views.LogoutView.as_view(
        template_name='shop/staff/logout.html',
        next_page='index'
    ), name='staff_logout'),
    
    # Custom product management URLs (staff only)
    path('manage/products/', views.custom_product_list_view, name='custom_product_list'),
    path('manage/add-product/', views.custom_product_add_view, name='custom_product_add'),
    path('manage/edit-product/<slug:slug>/', views.custom_product_edit_view, name='custom_product_edit'),
    path('manage/stock/', views.stock_management_view, name='stock_management'),
    
    # Order management URLs (staff only)
    path('manage/orders/', views.manage_orders, name='manage_orders'),
    path('manage/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('manage/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('manage/orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Public URLs
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('search/', views.search_results, name='search_results'),
    path('products/', views.products_view, name='products'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    
    # Image management URLs (staff only)
    path('manage/product/image/delete/', views.delete_product_image, name='delete_product_image'),
    path('manage/product/image/set-primary/', views.set_primary_image, name='set_primary_image'),
    path('manage/product/image/update-order/', views.update_image_order, name='update_image_order'),
    
    # Subcategory URL
    path('manage/get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('update-stock/<int:product_id>/', views.update_stock, name='update_stock'),
    
    # Stock management URLs (staff only)
    path('manage/stock/update/<int:product_id>/', views.update_stock, name='update_stock'),
    path('manage/stock/toggle-preorder/<int:product_id>/', views.toggle_preorder, name='toggle_preorder'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)