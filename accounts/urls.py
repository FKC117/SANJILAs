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
    path('receivables/<int:receivable_id>/edit/', views.edit_receivable, name='edit_receivable'),
    path('receivables/<int:receivable_id>/payment/', views.record_receivable_payment, name='record_receivable_payment'),
    path('payables/', views.payables, name='payables'),
    path('payables/<int:payable_id>/edit/', views.edit_payable, name='edit_payable'),
    path('payables/<int:payable_id>/payment/', views.record_payable_payment, name='record_payable_payment'),
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/payment/', views.record_expense_payment, name='record_expense_payment'),
    path('revenue/', views.revenue, name='revenue'),
    path('reports/', views.financial_reports, name='financial_reports'),
] 