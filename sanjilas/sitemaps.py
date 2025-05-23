from django.contrib.sitemaps import Sitemap
from shop.models import Product, ProductCategory, ProductSubCategory, AboutUs, SiteSettings, HeroContent


from django.urls import reverse

class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    
    def items(self):
        return Product.objects.filter(available=True)
    
    def lastmod(self, obj):
        return obj.updated_at

class ProductCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return ProductCategory.objects.all()
    
    def lastmod(self, obj):
        # Use the latest product update in this category
        latest_product = obj.category_products.order_by('-updated_at').first()
        return latest_product.updated_at if latest_product else None

class ProductSubCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        return ProductSubCategory.objects.all()
    
    def lastmod(self, obj):
        # Use the latest product update in this subcategory
        latest_product = obj.subcategory_products.order_by('-updated_at').first()
        return latest_product.updated_at if latest_product else None

class AboutUsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    
    def items(self):
        return AboutUs.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return ['index', 'about', 'contact']
    
    def location(self, item):
        return reverse(item)

# Dictionary of sitemaps
sitemaps = {
    'products': ProductSitemap,
    'categories': ProductCategorySitemap,
    'subcategories': ProductSubCategorySitemap,
    'about': AboutUsSitemap,
    'static': StaticViewSitemap,
}
    
    
