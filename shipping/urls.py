from django.urls import path
from . import views


urlpatterns = [
    path('api/orders/<int:order_id>/initiate-pathao/', views.initiate_pathao_order, name='initiate_pathao_order'),
    path('api/orders/<int:order_id>/reinitiate-pathao/', views.reinitiate_pathao_order, name='reinitiate_pathao_order'),
    path('api/webhook/pathao/', views.pathao_webhook, name='pathao_webhook'),
]


