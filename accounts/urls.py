from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('manage/products/', views.product_dashboard, name='product_dashboard'),
    path('manage/products/sales-data/', views.get_sales_data, name='sales_data'),
    path('manage/products/product-performance/', views.get_product_performance, name='product_performance'),
    path('dashboard/', views.accounting_dashboard, name='accounting_dashboard'),
    path('chart-of-accounts/', views.chart_of_accounts, name='chart_of_accounts'),
    path('journal-entries/', views.journal_entries, name='journal_entries'),
    path('receivables/', views.receivables, name='receivables'),
    path('payables/', views.payables, name='payables'),
    path('expenses/', views.expenses, name='expenses'),
    path('revenue/', views.revenue, name='revenue'),
    path('reports/', views.financial_reports, name='financial_reports'),
] 