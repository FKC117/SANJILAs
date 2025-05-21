from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from decimal import Decimal
from .models import Payable, Payment, ExpenseCategory
from .forms import PayableForm

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def payables(request):
    """View for managing payables"""
    if request.method == 'POST':
        form = PayableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payable created successfully.')
            return redirect('accounts:payables')
    else:
        form = PayableForm()
    
    payables = Payable.objects.select_related('supplier', 'expense_category').order_by('-date', '-created_at')
    expense_categories = ExpenseCategory.objects.filter(is_active=True).order_by('code')
    
    return render(request, 'accounts/payables.html', {
        'form': form,
        'payables': payables,
        'expense_categories': expense_categories
    })

@user_passes_test(is_superuser)
def edit_payable(request, payable_id):
    """View for editing an existing payable"""
    payable = get_object_or_404(Payable, id=payable_id)
    
    if request.method == 'POST':
        form = PayableForm(request.POST, instance=payable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payable updated successfully.')
            return redirect('accounts:payables')
    else:
        # For GET requests, just redirect back to the payables page
        # since editing is handled through a modal
        return redirect('accounts:payables')

@user_passes_test(is_superuser)
def record_payable_payment(request, payable_id):
    """View for recording payment for a payable"""
    payable = get_object_or_404(Payable, id=payable_id)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method')
        reference = request.POST.get('reference')
        notes = request.POST.get('notes')
        
        if amount > payable.balance:
            messages.error(request, 'Payment amount cannot exceed the payable balance.')
            return redirect('accounts:payables')
            
        # Create payment record
        payment = Payment.objects.create(
            payable=payable,
            amount=amount,
            date=payment_date,
            method=payment_method,
            reference=reference,
            notes=notes,
            created_by=request.user
        )
        
        # Update payable
        payable.paid_amount += amount
        if payable.paid_amount >= payable.amount:
            payable.status = 'PAID'
        elif payable.paid_amount > 0:
            payable.status = 'PARTIAL'
        payable.save()
        
        messages.success(request, 'Payment recorded successfully.')
        return redirect('accounts:payables')
        
    return redirect('accounts:payables') 