from django import forms
from .models import Product, ProductImage
from django.forms.models import inlineformset_factory
from decimal import Decimal

class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'subcategory', 'heading', 'short_description',
            'description', 'selling_price', 'discount_percentage', 'stock', 'show_price',
            'available', 'featured', 'best_selling', 'trending', 'new_arrival', 'sku',
            'preorder', 'video_url', 'buying_price'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'buying_price': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['subcategory'].required = True
        self.fields['selling_price'].required = True
        self.fields['stock'].required = True
        # Set default value for buying_price
        self.initial['buying_price'] = Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        # Ensure buying_price is set
        if 'buying_price' not in cleaned_data or cleaned_data['buying_price'] is None:
            cleaned_data['buying_price'] = Decimal('0.00')
        return cleaned_data

class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'subcategory', 'heading', 'short_description',
            'description', 'selling_price', 'discount_percentage', 'stock', 'show_price',
            'available', 'featured', 'best_selling', 'trending', 'new_arrival', 'sku',
            'preorder', 'video_url', 'buying_price'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'buying_price': forms.HiddenInput(),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
         model = ProductImage
         fields = ['image', 'alt_text', 'order']
         widgets = {
             'order': forms.HiddenInput(),  # Hide the order field as we'll set it automatically
         }

    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.fields['image'].required = False
         self.fields['order'].required = False
         # Set initial order value for new forms
         if not self.instance.pk and hasattr(self.instance, 'product') and self.instance.product:
             # Get the next order value only if we have a product
             last_order = ProductImage.objects.filter(product=self.instance.product).order_by('-order').first()
             self.initial['order'] = (last_order.order + 1) if last_order else 0
         else:
             # For new forms without a product, set order to 0
             self.initial['order'] = 0

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True,
    min_num=1,
    validate_min=True
)