from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop import views as shop_views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', shop_views.index, name='index'),  # Root URL goes to the shop index
    path('shop/', include('shop.urls')),
    path('order/', include('order.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)