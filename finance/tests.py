from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from order.models import Order, OrderItem
from shop.models import Product, Category
from .services import (
    FinancialCalculationService,
    get_date_range,
    calculate_order_totals,
    calculate_profit_margins,
    get_status_breakdown,
    get_payment_method_breakdown,
    get_product_breakdown,
    get_daily_breakdown,
    calculate_tax_amount,
    calculate_discount_amount,
    FinancialValidationError
)

class FinancialCalculationsTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test category
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name="Test Product 1",
            category=self.category,
            buying_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            stock=10
        )
        
        self.product2 = Product.objects.create(
            name="Test Product 2",
            category=self.category,
            buying_price=Decimal('200.00'),
            selling_price=Decimal('300.00'),
            stock=5
        )
        
        # Create test orders
        self.order1 = Order.objects.create(
            customer_name="Test Customer 1",
            shipping_address="Test Address 1",
            total_amount=Decimal('150.00'),
            shipping_cost=Decimal('10.00'),
            status='delivered',
            payment_method='cash'
        )
        
        self.order2 = Order.objects.create(
            customer_name="Test Customer 2",
            shipping_address="Test Address 2",
            total_amount=Decimal('300.00'),
            shipping_cost=Decimal('15.00'),
            status='shipped',
            payment_method='card'
        )
        
        # Create order items
        OrderItem.objects.create(
            order=self.order1,
            product=self.product1,
            quantity=1,
            unit_price=Decimal('150.00')
        )
        
        OrderItem.objects.create(
            order=self.order2,
            product=self.product2,
            quantity=1,
            unit_price=Decimal('300.00')
        )

    def test_get_date_range(self):
        """Test date range calculation"""
        # Test default range
        date_range = get_date_range()
        self.assertEqual(
            date_range.end_date,
            timezone.now().date()
        )
        self.assertEqual(
            date_range.start_date,
            timezone.now().date() - timedelta(days=30)
        )
        
        # Test custom range
        start_date = timezone.now().date() - timedelta(days=10)
        end_date = timezone.now().date()
        date_range = get_date_range(start_date, end_date)
        self.assertEqual(date_range.start_date, start_date)
        self.assertEqual(date_range.end_date, end_date)
        
        # Test invalid range
        with self.assertRaises(FinancialValidationError):
            get_date_range(end_date, start_date)

    def test_calculate_order_totals(self):
        """Test order totals calculation"""
        orders = Order.objects.all()
        totals = calculate_order_totals(orders)
        
        self.assertEqual(totals['total_amount'], Decimal('450.00'))
        self.assertEqual(totals['total_shipping'], Decimal('25.00'))
        self.assertEqual(totals['total_cost'], Decimal('300.00'))

    def test_calculate_profit_margins(self):
        """Test profit margin calculations"""
        margins = calculate_profit_margins(
            Decimal('450.00'),
            Decimal('300.00'),
            Decimal('25.00')
        )
        
        self.assertEqual(margins['gross_profit'], Decimal('150.00'))
        self.assertEqual(margins['net_profit'], Decimal('125.00'))
        self.assertEqual(margins['gross_margin'], Decimal('33.33'))
        self.assertEqual(margins['net_margin'], Decimal('27.78'))

    def test_get_status_breakdown(self):
        """Test order status breakdown"""
        orders = Order.objects.all()
        breakdown = get_status_breakdown(orders)
        
        self.assertEqual(breakdown['delivered']['count'], 1)
        self.assertEqual(breakdown['shipped']['count'], 1)
        self.assertEqual(breakdown['delivered']['amount'], Decimal('150.00'))
        self.assertEqual(breakdown['shipped']['amount'], Decimal('300.00'))

    def test_get_payment_method_breakdown(self):
        """Test payment method breakdown"""
        orders = Order.objects.all()
        breakdown = get_payment_method_breakdown(orders)
        
        self.assertEqual(breakdown['cash']['count'], 1)
        self.assertEqual(breakdown['card']['count'], 1)
        self.assertEqual(breakdown['cash']['amount'], Decimal('150.00'))
        self.assertEqual(breakdown['card']['amount'], Decimal('300.00'))

    def test_get_product_breakdown(self):
        """Test product breakdown"""
        order_items = OrderItem.objects.all()
        breakdown = get_product_breakdown(order_items)
        
        self.assertEqual(breakdown[self.product1.id]['quantity_sold'], 1)
        self.assertEqual(breakdown[self.product2.id]['quantity_sold'], 1)
        self.assertEqual(breakdown[self.product1.id]['total_sales'], Decimal('150.00'))
        self.assertEqual(breakdown[self.product2.id]['total_sales'], Decimal('300.00'))

    def test_get_daily_breakdown(self):
        """Test daily breakdown"""
        orders = Order.objects.all()
        breakdown = get_daily_breakdown(orders)
        
        self.assertEqual(len(breakdown), 1)  # All orders created on same day
        self.assertEqual(breakdown[0]['total_sales'], Decimal('450.00'))
        self.assertEqual(breakdown[0]['order_count'], 2)

    def test_calculate_tax_amount(self):
        """Test tax calculation"""
        tax_amount = calculate_tax_amount(Decimal('100.00'), Decimal('0.1'))
        self.assertEqual(tax_amount, Decimal('10.00'))
        
        with self.assertRaises(FinancialValidationError):
            calculate_tax_amount('invalid', Decimal('0.1'))

    def test_calculate_discount_amount(self):
        """Test discount calculation"""
        discount_amount = calculate_discount_amount(Decimal('100.00'), Decimal('0.2'))
        self.assertEqual(discount_amount, Decimal('20.00'))
        
        with self.assertRaises(FinancialValidationError):
            calculate_discount_amount('invalid', Decimal('0.2'))

    def test_financial_calculation_service(self):
        """Test FinancialCalculationService methods"""
        # Test sales summary
        sales_summary = FinancialCalculationService.get_sales_summary()
        self.assertEqual(sales_summary['total_sales'], Decimal('450.00'))
        self.assertEqual(sales_summary['total_orders'], 2)
        
        # Test product summary
        product_summary = FinancialCalculationService.get_product_sales_summary()
        self.assertEqual(
            len(product_summary['product_sales']),
            2
        )
        
        # Test payment summary
        payment_summary = FinancialCalculationService.get_payment_summary()
        self.assertEqual(
            payment_summary['payment_summary']['cash']['amount'],
            Decimal('150.00')
        )
        
        # Test profit summary
        profit_summary = FinancialCalculationService.get_profit_summary()
        self.assertEqual(profit_summary['total_sales'], Decimal('450.00'))
        self.assertEqual(profit_summary['total_cost'], Decimal('300.00'))
        
        # Test daily summary
        daily_summary = FinancialCalculationService.get_daily_sales_summary()
        self.assertEqual(len(daily_summary['daily_sales']), 1)
        self.assertEqual(
            daily_summary['daily_sales'][0]['total_sales'],
            Decimal('450.00')
        )
