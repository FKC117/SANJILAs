# finance/services.py

from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from order.models import Order, OrderItem
from shop.models import Product
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.db.models.functions import TruncDate

@dataclass
class DateRange:
    """Data class for date range with validation"""
    start_date: timezone.datetime.date
    end_date: timezone.datetime.date

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date")

class FinancialValidationError(Exception):
    """Custom exception for financial calculation errors"""
    pass

def validate_decimal(value: Union[str, float, Decimal], field_name: str) -> Decimal:
    """
    Validate and convert value to Decimal
    
    Args:
        value: Value to convert
        field_name: Name of the field for error message
        
    Returns:
        Decimal value
        
    Raises:
        FinancialValidationError: If value is invalid
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise FinancialValidationError(f"Invalid {field_name}: {value}")

def get_date_range(
    start_date: Optional[timezone.datetime.date] = None,
    end_date: Optional[timezone.datetime.date] = None,
    days: int = 30
) -> DateRange:
    """
    Get validated date range for financial calculations
    
    Args:
        start_date: Start date (optional)
        end_date: End date (optional)
        days: Number of days to look back if start_date not provided
        
    Returns:
        DateRange object with validated dates
        
    Raises:
        FinancialValidationError: If dates are invalid
    """
    try:
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=days)
        return DateRange(start_date=start_date, end_date=end_date)
    except Exception as e:
        raise FinancialValidationError(f"Invalid date range: {str(e)}")

def calculate_order_totals(orders: QuerySet) -> Dict[str, Decimal]:
    """
    Calculate totals for a set of orders
    
    Args:
        orders: QuerySet of Order objects
        
    Returns:
        Dictionary containing total_amount, total_cost, and total_shipping
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        total_amount = orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        total_cost = Decimal('0')
        total_shipping = orders.aggregate(
            total=Sum('shipping_cost')
        )['total'] or Decimal('0')
        
        for order in orders:
            for item in order.items.all():
                total_cost += item.quantity * item.product.buying_price
        
        return {
            'total_amount': validate_decimal(total_amount, 'total_amount'),
            'total_cost': validate_decimal(total_cost, 'total_cost'),
            'total_shipping': validate_decimal(total_shipping, 'total_shipping')
        }
    except Exception as e:
        raise FinancialValidationError(f"Error calculating order totals: {str(e)}")

def calculate_profit_margins(
    sales: Union[str, float, Decimal],
    cost: Union[str, float, Decimal],
    shipping: Union[str, float, Decimal] = Decimal('0')
) -> Dict[str, Decimal]:
    """
    Calculate profit margins and percentages
    
    Args:
        sales: Total sales amount
        cost: Total cost amount
        shipping: Total shipping cost
        
    Returns:
        Dictionary containing gross_profit, net_profit, gross_margin, and net_margin
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        sales = validate_decimal(sales, 'sales')
        cost = validate_decimal(cost, 'cost')
        shipping = validate_decimal(shipping, 'shipping')
        
        gross_profit = sales - cost
        net_profit = gross_profit - shipping
        
        gross_margin = (gross_profit / sales * 100) if sales > 0 else Decimal('0')
        net_margin = (net_profit / sales * 100) if sales > 0 else Decimal('0')
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'gross_margin': gross_margin,
            'net_margin': net_margin
        }
    except Exception as e:
        raise FinancialValidationError(f"Error calculating profit margins: {str(e)}")

def get_status_breakdown(orders: QuerySet) -> Dict[str, Dict[str, Union[Decimal, int]]]:
    """
    Get breakdown of orders by status
    
    Args:
        orders: QuerySet of Order objects
        
    Returns:
        Dictionary with status-wise totals and counts
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        status_totals = {
            'pending': {'amount': Decimal('0'), 'count': 0},
            'processing': {'amount': Decimal('0'), 'count': 0},
            'shipped': {'amount': Decimal('0'), 'count': 0},
            'delivered': {'amount': Decimal('0'), 'count': 0},
            'cancelled': {'amount': Decimal('0'), 'count': 0},
            'returned': {'amount': Decimal('0'), 'count': 0},
            'refunded': {'amount': Decimal('0'), 'count': 0}
        }
        
        for status in status_totals.keys():
            status_orders = orders.filter(status=status)
            status_totals[status]['amount'] = validate_decimal(
                status_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
                f'{status}_amount'
            )
            status_totals[status]['count'] = status_orders.count()
        
        return status_totals
    except Exception as e:
        raise FinancialValidationError(f"Error calculating status breakdown: {str(e)}")

def get_payment_method_breakdown(orders: QuerySet) -> Dict[str, Dict[str, Union[Decimal, int]]]:
    """
    Get breakdown of orders by payment method
    
    Args:
        orders: QuerySet of Order objects
        
    Returns:
        Dictionary with payment method-wise totals and counts
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        payment_summary = {}
        for method in dict(Order.PAYMENT_METHOD_CHOICES).keys():
            method_orders = orders.filter(payment_method=method)
            payment_summary[method] = {
                'amount': validate_decimal(
                    method_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
                    f'{method}_amount'
                ),
                'count': method_orders.count()
            }
        return payment_summary
    except Exception as e:
        raise FinancialValidationError(f"Error calculating payment method breakdown: {str(e)}")

def get_product_breakdown(order_items: QuerySet) -> Dict[int, Dict]:
    """
    Get breakdown of sales by product
    
    Args:
        order_items: QuerySet of OrderItem objects
        
    Returns:
        Dictionary with product-wise sales, costs, and profits
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        product_sales = {}
        for item in order_items:
            product = item.product
            if product.id not in product_sales:
                product_sales[product.id] = {
                    'product': product,
                    'quantity_sold': 0,
                    'total_sales': Decimal('0'),
                    'total_cost': Decimal('0'),
                    'profit': Decimal('0')
                }
            
            product_sales[product.id]['quantity_sold'] += item.quantity
            product_sales[product.id]['total_sales'] += validate_decimal(
                item.quantity * item.unit_price,
                'item_total'
            )
            product_sales[product.id]['total_cost'] += validate_decimal(
                item.quantity * product.buying_price,
                'item_cost'
            )
            product_sales[product.id]['profit'] = (
                product_sales[product.id]['total_sales'] - 
                product_sales[product.id]['total_cost']
            )
        
        return product_sales
    except Exception as e:
        raise FinancialValidationError(f"Error calculating product breakdown: {str(e)}")

def get_daily_breakdown(orders: QuerySet) -> List[Dict]:
    """
    Get daily breakdown of orders
    
    Args:
        orders: QuerySet of Order objects
        
    Returns:
        List of dictionaries with daily totals and counts
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        return list(orders.values('order_date__date').annotate(
            total_sales=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('order_date__date'))
    except Exception as e:
        raise FinancialValidationError(f"Error calculating daily breakdown: {str(e)}")

def calculate_tax_amount(
    amount: Union[str, float, Decimal],
    tax_rate: Union[str, float, Decimal]
) -> Decimal:
    """
    Calculate tax amount
    
    Args:
        amount: Base amount
        tax_rate: Tax rate as decimal (e.g., 0.1 for 10%)
        
    Returns:
        Tax amount
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        amount = validate_decimal(amount, 'amount')
        tax_rate = validate_decimal(tax_rate, 'tax_rate')
        return amount * tax_rate
    except Exception as e:
        raise FinancialValidationError(f"Error calculating tax: {str(e)}")

def calculate_discount_amount(
    amount: Union[str, float, Decimal],
    discount_rate: Union[str, float, Decimal]
) -> Decimal:
    """
    Calculate discount amount
    
    Args:
        amount: Base amount
        discount_rate: Discount rate as decimal (e.g., 0.1 for 10%)
        
    Returns:
        Discount amount
        
    Raises:
        FinancialValidationError: If calculation fails
    """
    try:
        amount = validate_decimal(amount, 'amount')
        discount_rate = validate_decimal(discount_rate, 'discount_rate')
        return amount * discount_rate
    except Exception as e:
        raise FinancialValidationError(f"Error calculating discount: {str(e)}")

class FinancialCalculationService:
    """Service class for financial calculations"""
    
    @staticmethod
    def get_sales_summary(
        start_date: Optional[timezone.datetime.date] = None,
        end_date: Optional[timezone.datetime.date] = None
    ) -> Dict:
        """
        Get comprehensive sales summary including all order statuses
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary containing sales summary
            
        Raises:
            FinancialValidationError: If calculation fails
        """
        try:
            date_range = get_date_range(start_date, end_date)
            
            orders = Order.objects.filter(
                order_date__date__range=[date_range.start_date, date_range.end_date]
            )
            
            status_breakdown = get_status_breakdown(orders)
            totals = calculate_order_totals(orders)
            
            return {
                'status_breakdown': status_breakdown,
                'total_sales': totals['total_amount'],
                'total_orders': sum(item['count'] for item in status_breakdown.values()),
                'period': {
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date
                }
            }
        except Exception as e:
            raise FinancialValidationError(f"Error in sales summary: {str(e)}")

    @staticmethod
    def get_product_sales_summary(
        start_date: Optional[timezone.datetime.date] = None,
        end_date: Optional[timezone.datetime.date] = None
    ) -> Dict:
        """
        Get sales summary by product
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary containing product sales summary
            
        Raises:
            FinancialValidationError: If calculation fails
        """
        try:
            date_range = get_date_range(start_date, end_date)
            
            order_items = OrderItem.objects.filter(
                order__order_date__date__range=[date_range.start_date, date_range.end_date],
                order__status__in=['delivered', 'shipped']
            ).select_related('product', 'order')
            
            product_sales = get_product_breakdown(order_items)
            
            return {
                'product_sales': product_sales,
                'period': {
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date
                }
            }
        except Exception as e:
            raise FinancialValidationError(f"Error in product sales summary: {str(e)}")

    @staticmethod
    def get_payment_summary(
        start_date: Optional[timezone.datetime.date] = None,
        end_date: Optional[timezone.datetime.date] = None
    ) -> Dict:
        """
        Get payment method summary
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary containing payment summary
            
        Raises:
            FinancialValidationError: If calculation fails
        """
        try:
            date_range = get_date_range(start_date, end_date)
            
            orders = Order.objects.filter(
                order_date__date__range=[date_range.start_date, date_range.end_date]
            )
            
            payment_summary = get_payment_method_breakdown(orders)
            
            return {
                'payment_summary': payment_summary,
                'period': {
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date
                }
            }
        except Exception as e:
            raise FinancialValidationError(f"Error in payment summary: {str(e)}")

    @staticmethod
    def get_profit_summary(
        start_date: Optional[timezone.datetime.date] = None,
        end_date: Optional[timezone.datetime.date] = None
    ) -> Dict:
        """
        Get profit summary including costs and margins
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary containing profit summary
            
        Raises:
            FinancialValidationError: If calculation fails
        """
        try:
            date_range = get_date_range(start_date, end_date)
            
            orders = Order.objects.filter(
                order_date__date__range=[date_range.start_date, date_range.end_date],
                status__in=['delivered', 'shipped']
            )
            
            totals = calculate_order_totals(orders)
            margins = calculate_profit_margins(
                totals['total_amount'],
                totals['total_cost'],
                totals['total_shipping']
            )
            
            return {
                'total_sales': totals['total_amount'],
                'total_cost': totals['total_cost'],
                'total_shipping': totals['total_shipping'],
                **margins,
                'period': {
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date
                }
            }
        except Exception as e:
            raise FinancialValidationError(f"Error in profit summary: {str(e)}")

    @staticmethod
    def get_daily_sales_summary(
        start_date: Optional[timezone.datetime.date] = None,
        end_date: Optional[timezone.datetime.date] = None
    ) -> Dict:
        """
        Get daily sales breakdown
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary containing daily sales summary
            
        Raises:
            FinancialValidationError: If calculation fails
        """
        try:
            date_range = get_date_range(start_date, end_date)
            
            orders = Order.objects.filter(
                order_date__date__range=[date_range.start_date, date_range.end_date]
            )
            
            daily_sales = get_daily_breakdown(orders)
            
            return {
                'daily_sales': daily_sales,
                'period': {
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date
                }
            }
        except Exception as e:
            raise FinancialValidationError(f"Error in daily sales summary: {str(e)}")

    @staticmethod
    def calculate_profit(sales, expenses):
        return sales - expenses

    @staticmethod
    def calculate_tax(amount, tax_rate):
        return amount * tax_rate

class ReportGenerationService:
    @staticmethod
    def generate_profit_loss(start_date, end_date):
        # Implementation
        return None

    @staticmethod
    def generate_balance_sheet(date):
        # Implementation
        return None