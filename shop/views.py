from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import *



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .forms import ProductCreateForm, ProductEditForm, ProductImageFormSet

@staff_member_required
def custom_product_add_view(request):
    if request.method == 'POST':
        product_form = ProductCreateForm(request.POST, request.FILES)
        if product_form.is_valid():
            product = product_form.save()
            return redirect('custom_product_edit', product.slug)
    else:
        product_form = ProductCreateForm()

    context = {
        'product_form': product_form,
        'title': 'Add New Product',
    }
    return render(request, 'shop/custom_product_add.html', context)

@staff_member_required
def custom_product_edit_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        product_form = ProductEditForm(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)

        if product_form.is_valid() and image_formset.is_valid():
            product = product_form.save()
            image_formset.save()
            return redirect('custom_product_edit', product.slug)
    else:
        product_form = ProductEditForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)

    context = {
        'product_form': product_form,
        'image_formset': image_formset,
        'product': product,
        'title': f'Edit Product: {product.name}',
    }
    return render(request, 'shop/custom_product_edit.html', context)



def index(request):
    new_arrival = Product.objects.filter(new_arrival=True).order_by('-id')[:8]
    best_selling = Product.objects.filter(best_selling=True).order_by('-id')[:8]
    trending = Product.objects.filter(trending=True).order_by('-id')[:8]
    categories = ProductCategory.objects.all()
    subcategories = ProductSubCategory.objects.all()[:8]
    hero_content = HeroContent.objects.filter(publish=True).first()
    hero_images = HeroImage.objects.filter(hero_content=hero_content).order_by('order') if hero_content else None
    context = {
        'hero_content': hero_content,
        'hero_images': hero_images,
        'new_arrival': new_arrival,
        'best_selling': best_selling,
        'trending': trending,
        'categories': categories,
        'subcategories': subcategories,
    }
    return render(request, 'shop/index.html', context)