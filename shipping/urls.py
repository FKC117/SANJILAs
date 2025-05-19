from django.urls import path
from . import views


urlpatterns = [
    path('api/orders/<int:order_id>/initiate-pathao/', views.initiate_pathao_order, name='initiate_pathao_order'),
]


