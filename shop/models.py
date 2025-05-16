# shop/models.py
from django.db import models
from django.utils.text import slugify
import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
#from django_summernote.fields import SummernoteTextField



class HeroContent(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    button_text = models.CharField(max_length=255)
    button_url = models.URLField()
    publish = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class HeroImage(models.Model):
    hero_content = models.ForeignKey(HeroContent, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='hero_images/')
    order = models.PositiveIntegerField(default=0, help_text="Order of the image in the slider")
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image {self.order} for {self.hero_content.title}"
    

class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductSubCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ManyToManyField(ProductCategory, related_name='sub_categories')
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        verbose_name = 'Product SubCategory'
        verbose_name_plural = 'Product SubCategories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(ProductCategory, related_name='category_products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(ProductSubCategory, related_name='subcategory_products', on_delete=models.CASCADE)
    heading = models.CharField(max_length=500, blank=True, null=True, help_text="Optional()")
    short_description = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(default="")
    suppliers = models.ManyToManyField('Supplier', through='ProductSupplier', blank=True, related_name='supplied_products')
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    show_price = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    margin = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    best_selling = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    new_arrival = models.BooleanField(default=False)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    preorder = models.BooleanField(default=False)
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Optional Video link from youtube or facebook")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def first_image(self):
        """Get the first image URL or None if no images are available."""
        try:
            first_image = self.images.first()
            if first_image and first_image.image:
                return first_image.image.url
            return None
        except (AttributeError, ValueError) as e:
            # Log error and return None if anything fails
            print(f"Error getting image for product {self.id}: {e}")
            return None
    
    def get_selling_price(self):
        """Get the actual selling price (discount_price if available, otherwise selling_price)."""
        try:
            if self.discount_price is not None:
                return self.discount_price
            elif self.selling_price is not None:
                return self.selling_price
            else:
                # Fallback to zero if no price is available
                return 0
        except Exception as e:
            print(f"Error calculating selling price for product {self.id}: {e}")
            return 0

    @property
    def get_discounted_price(self):
        """Calculate the discounted price based on the selling price and discount percentage."""
        try:
            if self.discount_percentage and self.discount_percentage > 0:
                discount_amount = (self.selling_price * self.discount_percentage) / 100
                return self.selling_price - discount_amount
            return self.selling_price
        except Exception as e:
            print(f"Error calculating discounted price for product {self.id}: {e}")
            return self.selling_price

    def admin_photo(self):
        url = self.first_image
        if url:
            return f'<img src="{url}" style="max-height: 50px; max-width: 50px;" />'
        return '(No Image)'

    admin_photo.short_description = 'Image'
    admin_photo.allow_tags = True

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def generate_sku(self):
        category_abbr = ''.join(word[0].upper() for word in self.category.name.split())[:3]  # First 3 initials of category
        unique_id = str(uuid.uuid4().hex[:8]).upper()  # Using 8 hex characters for higher uniqueness
        return f"{category_abbr}-{unique_id}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = self.generate_sku()
        # Calculate the discounted price when discount percentage is given
        if self.discount_percentage is not None and self.discount_percentage > 0 and self.selling_price is not None:
            discount_percentage_decimal = Decimal(self.discount_percentage) / Decimal('100.00')
            discount_amount = discount_percentage_decimal * self.selling_price
            self.discount_price = self.selling_price - discount_amount
        else:
            self.discount_price = None
        # Calculate the margin if buying price is provided
        if self.buying_price is not None and self.selling_price is not None:
            self.margin = self.selling_price - self.buying_price
        else:
            self.margin = None
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"

class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # product = models.ManyToManyField(Product, blank=True, related_name='supplier_product')
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
    def __str__(self):
        return self.name
    


class ProductSupplier(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time = models.PositiveIntegerField(blank=True, null=True, help_text="Lead time in days")

    class Meta:
        unique_together = ('product', 'supplier')
    def __str__(self):
        return f"{self.supplier.name} supplies {self.product.name} at BDT {self.buying_price}"

class SiteSettings(models.Model):
    """
    Model to store site-wide settings including logos and branding elements.
    This model is designed to have only one instance (singleton pattern).
    """
    site_name = models.CharField(max_length=100, default="Sanjilas Shop")
    site_description = models.TextField(blank=True, help_text="Brief description of the website for SEO")
    
    # Logo fields for different contexts
    navbar_logo = models.ImageField(
        upload_to='site_logos/',
        help_text="Logo for the navigation bar (recommended size: 200x50px)",
        blank=True
    )
    footer_logo = models.ImageField(
        upload_to='site_logos/',
        help_text="Logo for the footer (recommended size: 200x50px)",
        blank=True
    )
    favicon = models.ImageField(
        upload_to='site_logos/',
        help_text="Favicon for the website (recommended size: 32x32px)",
        blank=True
    )
    
    # Contact Information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True, help_text="YouTube channel or video URL")
    threads_url = models.URLField(blank=True, help_text="Threads profile URL")
    
    # Meta Information
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for SEO")
    meta_description = models.TextField(blank=True, help_text="Meta description for SEO")
    
    # Footer Text
    footer_text = models.TextField(blank=True, help_text="Text to display in the footer")
    copyright_text = models.CharField(max_length=255, default="© 2024 Sanjilas Shop. All rights reserved.")
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """
        Get or create the single instance of SiteSettings.
        This ensures we always have exactly one settings object.
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure only one instance exists
        """
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError('There can be only one SiteSettings instance')
        super().save(*args, **kwargs)


