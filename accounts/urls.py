from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('manage/products/', views.product_dashboard, name='product_dashboard'),
    path('manage/products/sales-data/', views.get_sales_data, name='sales_data'),
    path('manage/products/product-performance/', views.get_product_performance, name='product_performance'),
] 