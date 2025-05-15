from django import forms
from .models import Product, ProductImage

class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('slug', 'sku')

class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('slug', 'sku')

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'id'] # Include 'id' for editing existing images
        widgets = {
            'id': forms.HiddenInput(),
        }

ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,  # Number of empty forms for new images
    can_delete=True
)