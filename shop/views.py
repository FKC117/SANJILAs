from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db.models import Q, Case, When, IntegerField
import json

from .models import Product, ProductCategory, ProductImage, HeroContent, HeroImage, ProductSubCategory, SiteSettings
from .forms import ProductCreateForm, ProductEditForm, ProductImageFormSet

# Create a context processor to make categories available in all templates
def categories_processor(request):
    """
    Context processor to make categories available in all templates
    """
    categories = ProductCategory.objects.all()
    return {
        'categories': categories,
    }

def site_settings_processor(request):
    """
    Context processor to make site settings available in all templates
    """
    settings = SiteSettings.get_settings()
    return {
        'site_settings': settings,
    }

@staff_member_required
def custom_product_add_view(request):
    if request.method == 'POST':
        product_form = ProductCreateForm(request.POST, request.FILES)
        image_formset = ProductImageFormSet(request.POST, request.FILES)
        
        if product_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the product first
                    product = product_form.save(commit=False)
                    # Generate slug and SKU
                    product.slug = slugify(product.name)
                    product.sku = product.generate_sku()
                    product.save()
                    
                    # Now save the image formset
                    image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
                    if image_formset.is_valid():
                        # Set order for each image before saving
                        for i, form in enumerate(image_formset.forms):
                            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                                form.instance.order = i
                        image_formset.save()
                        messages.success(request, f'Product "{product.name}" was successfully created.')
                        return redirect('custom_product_list')
                    else:
                        # If image formset is invalid, delete the product and raise error
                        product.delete()
                        for error in image_formset.errors:
                            messages.error(request, f'Image error: {error}')
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        else:
            # Display form errors
            for field, errors in product_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        product_form = ProductCreateForm()
        image_formset = ProductImageFormSet()

    context = {
        'product_form': product_form,
        'image_formset': image_formset,
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
            # Set order for each image before saving
            for i, form in enumerate(image_formset.forms):
                if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                    form.instance.order = i
            image_formset.save()
            messages.success(request, f'Product "{product.name}" was successfully updated.')
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

@staff_member_required
def custom_product_list_view(request):
    products = Product.objects.all().order_by('-created_at')
    context = {
        'products': products,
        'title': 'Manage Products',
    }
    return render(request, 'shop/custom_product_list.html', context)

@staff_member_required
def set_primary_image(request):
    # This feature is not implemented because the model does not support a primary image
    return JsonResponse({'status': 'error', 'message': 'Primary image feature not implemented.'}, status=400)

def index(request):
    # Get hero content
    hero_content = HeroContent.objects.filter(publish=True).first()
    hero_images = HeroImage.objects.filter(hero_content=hero_content).order_by('order') if hero_content else None
    
    # New Arrivals Section (8 latest products)
    new_arrival_page = request.GET.get('new_arrival_page', 1)
    new_arrival_products = Product.objects.filter(available=True).order_by('-created_at')
    new_arrival_paginator = Paginator(new_arrival_products, 8)
    try:
        new_arrival = new_arrival_paginator.page(new_arrival_page)
    except (PageNotAnInteger, EmptyPage):
        new_arrival = new_arrival_paginator.page(1)
    
    # Trending Section
    trending_page = request.GET.get('trending_page', 1)
    trending_products = Product.objects.filter(trending=True, available=True).order_by('-id')
    trending_paginator = Paginator(trending_products, 8)
    try:
        trending = trending_paginator.page(trending_page)
    except (PageNotAnInteger, EmptyPage):
        trending = trending_paginator.page(1)
    
    # All Products Section
    products_page = request.GET.get('products_page', 1)
    all_products = Product.objects.filter(available=True).order_by('-created_at')
    products_paginator = Paginator(all_products, 8)
    try:
        products = products_paginator.page(products_page)
    except (PageNotAnInteger, EmptyPage):
        products = products_paginator.page(1)
    
    # Best Selling Section
    best_selling_page = request.GET.get('best_selling_page', 1)
    best_selling_products = Product.objects.filter(best_selling=True, available=True).order_by('-id')
    best_selling_paginator = Paginator(best_selling_products, 8)
    try:
        best_selling = best_selling_paginator.page(best_selling_page)
    except (PageNotAnInteger, EmptyPage):
        best_selling = best_selling_paginator.page(1)
    
    # Featured Section
    featured_page = request.GET.get('featured_page', 1)
    featured_products = Product.objects.filter(featured=True, available=True).order_by('-id')
    featured_paginator = Paginator(featured_products, 8)
    try:
        featured = featured_paginator.page(featured_page)
    except (PageNotAnInteger, EmptyPage):
        featured = featured_paginator.page(1)
    
    context = {
        'hero_content': hero_content,
        'hero_images': hero_images,
        'new_arrival': new_arrival,
        'trending': trending,
        'products': products,
        'best_selling': best_selling,
        'featured': featured,
    }
    return render(request, 'shop/index.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # Get related products using the same logic as cart view
    related_products = Product.objects.filter(
        Q(subcategory=product.subcategory) | Q(category=product.category),
        available=True
    ).exclude(
        id=product.id
    ).order_by(
        # Order by subcategory match first, then random
        Case(
            When(subcategory=product.subcategory, then=0),
            default=1,
            output_field=IntegerField(),
        ),
        '?'
    )[:4]  # Limit to 4 products
    
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'shop/product_detail.html', context)

def category_view(request, category_slug):
    category = get_object_or_404(ProductCategory, slug=category_slug)
    
    # Get subcategories for filtering
    subcategories = ProductSubCategory.objects.filter(category=category)
    
    # Initialize with all products in this category
    products_list = Product.objects.filter(category=category, available=True)
    
    # Apply subcategory filter if requested
    subcategory_slug = request.GET.get('subcategory')
    if subcategory_slug:
        subcategory = get_object_or_404(ProductSubCategory, slug=subcategory_slug)
        products_list = products_list.filter(subcategory=subcategory)
    
    # Apply sorting if requested
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price-low':
        products_list = products_list.order_by('selling_price')
    elif sort_by == 'price-high':
        products_list = products_list.order_by('-selling_price')
    elif sort_by == 'best-selling':
        products_list = products_list.filter(best_selling=True).order_by('-id')
    else:  # newest by default
        products_list = products_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products_list, 12)  # Show 12 products per page
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        products = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'products': products,
        'active_subcategory': subcategory_slug,
        'active_sort': sort_by,
    }
    return render(request, 'shop/category.html', context)

def search_results(request):
    query = request.GET.get('query', '')
    
    if query:
        # Search in product name and description
        products_list = Product.objects.filter(
            available=True
        ).filter(
            name__icontains=query
        ) | Product.objects.filter(
            available=True
        ).filter(
            description__icontains=query
        )
    else:
        products_list = Product.objects.none()
    
    # Pagination
    paginator = Paginator(products_list, 12)  # Show 12 products per page
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'query': query,
        'total_results': products_list.count(),
    }
    return render(request, 'shop/search_results.html', context)

@require_POST
def delete_product_image(request):
    image_id = request.POST.get('image_id')
    if image_id:
        try:
            image = ProductImage.objects.get(id=image_id)
            image.delete()
            return JsonResponse({'status': 'success'})
        except ProductImage.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Image not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'No image ID provided'}, status=400)

@require_POST
def update_image_order(request):
    try:
        data = json.loads(request.body)
        for item in data:
            image = ProductImage.objects.get(id=item['id'])
            image.order = item['order']
            image.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = ProductSubCategory.objects.filter(category_id=category_id)
        data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

def products_view(request):
    # Get all categories with their subcategories
    categories = ProductCategory.objects.prefetch_related('sub_categories').all()
    
    # Get filter parameters
    category_slug = request.GET.get('category')
    subcategory_slug = request.GET.get('subcategory')
    sort_by = request.GET.get('sort', 'newest')
    
    # Initialize products queryset
    products = Product.objects.filter(available=True)
    
    # Apply category filter if selected
    if category_slug:
        category = get_object_or_404(ProductCategory, slug=category_slug)
        products = products.filter(category=category)
        
        # Apply subcategory filter if selected
        if subcategory_slug:
            subcategory = get_object_or_404(ProductSubCategory, slug=subcategory_slug)
            products = products.filter(subcategory=subcategory)
    
    # Apply sorting
    if sort_by == 'price-low':
        products = products.order_by('selling_price')
    elif sort_by == 'price-high':
        products = products.order_by('-selling_price')
    elif sort_by == 'best-selling':
        products = products.filter(best_selling=True).order_by('-id')
    else:  # newest by default
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'categories': categories,
        'products': products,
        'active_category': category_slug,
        'active_subcategory': subcategory_slug,
        'active_sort': sort_by,
        'title': 'All Products',
    }
    return render(request, 'shop/products.html', context)