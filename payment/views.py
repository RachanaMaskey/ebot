from django.shortcuts import render
from cart.cart import Cart
from payment.forms import ShippingForm
from payment.models import ShippingAddress

def payment_success(request):
    return render(request,"payment/payment_success.html",{})

def checkout(request):
    #get the cart
    cart=Cart(request)
    cart_products=cart.get_prods
    quantities=cart.get_quants
    totals= cart.cart_total()
    sum=cart.total()
    if request.user.is_authenticated:
        #get current users shipping info
        shipping_user=ShippingAddress.objects.get(user__id=request.user.id)
        #checkout as logged in user
        shipping_form=ShippingForm(request.POST or None, instance=shipping_user)
        return render(request,"payment/checkout.html",{"cart_products": cart_products,"quantities":quantities,"totals":totals,"sum":sum,"shipping_form":shipping_form})
    else:
        #checkout as guest
        shipping_form=ShippingForm(request.POST or None)
        return render(request,"payment/checkout.html",{"cart_products": cart_products,"quantities":quantities,"totals":totals,"sum":sum,"shipping_form":shipping_form})
       
        

    

