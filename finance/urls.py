from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('products/', views.product_report, name='product_report'),
    path('profit/', views.profit_report, name='profit_report'),
]