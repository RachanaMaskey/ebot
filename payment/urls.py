from django.urls import path, include 
from .import views

urlpatterns = [
    path('checkout',views.checkout,name='checkout'),
    path('payment_success',views.payment_success,name='payment_success'),
    path('initiate_payment', views.initiate_payment, name='initiate_payment'),
    path('payment_failed', views.payment_failed, name='payment_failed'),
]