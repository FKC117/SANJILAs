from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .forms import ProductCreateForm, ProductEditForm, ProductImageFormSet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create a context processor to make categories available in all templates
def categories_processor(request):
    """
    Context processor to make categories available in all templates
    """
    categories = ProductCategory.objects.all()
    return {
        'categories': categories,
    }

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
    # Get featured products for each section
    new_arrival = Product.objects.filter(new_arrival=True, available=True).order_by('-created_at')[:12]
    best_selling = Product.objects.filter(best_selling=True, available=True).order_by('-id')[:12]
    trending = Product.objects.filter(trending=True, available=True).order_by('-id')[:12]
    
    # Get all available products for the main products section
    all_products = Product.objects.filter(available=True).order_by('-created_at')
    
    # Pagination for all products
    paginator = Paginator(all_products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Get hero content
    hero_content = HeroContent.objects.filter(publish=True).first()
    hero_images = HeroImage.objects.filter(hero_content=hero_content).order_by('order') if hero_content else None
    
    context = {
        'hero_content': hero_content,
        'hero_images': hero_images,
        'new_arrival': new_arrival,
        'best_selling': best_selling,
        'trending': trending,
        'products': products,  # Paginated all products
        'total_products': all_products.count(),
    }
    return render(request, 'shop/index.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Get related products based on the same category
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
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