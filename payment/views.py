from django.shortcuts import render
from cart.cart import Cart
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django.core.exceptions import ObjectDoesNotExist
import time


def checkout(request):
    #get the cart
    cart=Cart(request)
    cart_products=cart.get_prods
    quantities=cart.get_quants
    totals= cart.cart_total()
    sum=cart.total()
    # if request.user.is_authenticated:
    #     #get current users shipping info
    #     shipping_user=ShippingAddress.objects.get(user__id=request.user.id)
    #     #checkout as logged in user
    #     shipping_form=ShippingForm(request.POST or None, instance=shipping_user)
    #     return render(request,"payment/checkout.html",{"cart_products": cart_products,"quantities":quantities,"totals":totals,"sum":sum,"shipping_form":shipping_form})
    # else:
    #     #checkout as guest
    #     shipping_form=ShippingForm(request.POST or None)
    #     return render(request,"payment/checkout.html",{"cart_products": cart_products,"quantities":quantities,"totals":totals,"sum":sum,"shipping_form":shipping_form})
       
    # Generate unique pid using timestamp
    pid = f"{request.user.id}_{int(time.time())}" if request.user.is_authenticated else f"GUEST_{int(time.time())}"
    
    if request.user.is_authenticated:
        try:
            # Try to fetch the user's shipping info
            shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
            # Pre-fill form with existing data
            shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        except ObjectDoesNotExist:
            # Create a blank form if no shipping address exists
            shipping_form = ShippingForm(request.POST or None)

        return render(request, "payment/checkout.html", {
            "cart_products": cart_products,
            "quantities": quantities,
            "totals": totals,
            "sum": sum,
            "shipping_form": shipping_form,
        })
    
    # Handle guest checkout
    else:
        shipping_form = ShippingForm(request.POST or None)
        return render(request, "payment/checkout.html", {
            "cart_products": cart_products,
            "quantities": quantities,
            "totals": totals,
            "sum": sum,
            "pid": pid,
            "shipping_form": shipping_form,
        })



#for esewa

# import requests
from django.shortcuts import render, redirect
from django.conf import settings

def initiate_payment(request):
    if request.method == "POST":
        total_amount = request.POST.get("total_amount")
        order_id = f"TEST_{request.user.id}_{total_amount}"

        params = {
            'amt': total_amount,
            'pdc': 0,  # Promo Discount
            'psc': 0,  # Service Charge
            'txAmt': 0,  # Tax Amount
            'tAmt': total_amount,  # Total Amount
            'pid': order_id,  # Unique Product ID
            'scd': settings.ESEWA_MERCHANT_ID,  # Merchant ID
            'su': settings.ESEWA_RETURN_URL,  # Success URL
            'fu': settings.ESEWA_FAILED_URL,  # Failed URL
        }

        esewa_payment_url = f"{settings.ESEWA_DEMO_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return redirect(esewa_payment_url)



def payment_success(request):
    return render(request, "payment/payment_success.html", {})


def payment_failed(request):
    return render(request, "payment/payment_failed.html", {})

        

    

