from django.core.management.base import BaseCommand
from accounts.models import Account, ExpenseCategory

class Command(BaseCommand):
    help = 'Updates expense accounts to link them with their corresponding expense categories'

    def handle(self, *args, **options):
        # Define the mapping of account codes to expense categories
        mappings = {
            '5000': 'Operational',
            '5100': 'Shipping',
            '5150': 'COD Charges',
            '5200': 'Marketing',
            '5300': 'Salary',
            '5400': 'Rent',
            '5500': 'Utilities',
            '5600': 'Website',
            '5700': 'Payment Processing',
            '5900': 'Other'
        }

        # Update each account
        for code, category_name in mappings.items():
            try:
                account = Account.objects.get(code=code, type='expense')
                category = ExpenseCategory.objects.get(code=code)
                account.expense_category = category
                account.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully linked account {account.name} ({code}) to category {category.name}'
                    )
                )
            except Account.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Account with code {code} not found')
                )
            except ExpenseCategory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Expense category with code {code} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating account {code}: {str(e)}')
                ) 