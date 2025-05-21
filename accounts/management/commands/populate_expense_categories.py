from django.core.management.base import BaseCommand
from accounts.models import ExpenseCategory

class Command(BaseCommand):
    help = 'Populates the ExpenseCategory model with default values'

    def handle(self, *args, **options):
        # Define default expense categories with codes matching Chart of Accounts
        default_categories = [
            {'name': 'Operational', 'code': '5000', 'description': 'General operational expenses'},
            {'name': 'Salary', 'code': '5300', 'description': 'Employee salaries and benefits'},
            {'name': 'Rent', 'code': '5400', 'description': 'Office and warehouse rent'},
            {'name': 'Utilities', 'code': '5500', 'description': 'Electricity, water, and other utilities'},
            {'name': 'Shipping', 'code': '5100', 'description': 'Cost of shipping products'},
            {'name': 'COD Charges', 'code': '5150', 'description': 'Cash on Delivery charges (0.5% of product price)'},
            {'name': 'Marketing', 'code': '5200', 'description': 'Advertising and promotion costs'},
            {'name': 'Website', 'code': '5600', 'description': 'Website hosting and maintenance'},
            {'name': 'Payment Processing', 'code': '5700', 'description': 'Credit card and payment gateway fees'},
            {'name': 'Other', 'code': '5900', 'description': 'Other miscellaneous expenses'},
        ]

        # Create categories if they don't exist
        for category in default_categories:
            ExpenseCategory.objects.get_or_create(
                code=category['code'],
                defaults={
                    'name': category['name'],
                    'description': category['description'],
                    'is_active': True
                }
            )
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(default_categories)} expense categories')) 