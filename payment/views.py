from django.shortcuts import render,redirect
from cart.cart import Cart
from payment.forms import ShippingForm,PaymentForm
from payment.models import ShippingAddress,Order,OrderItem
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import time
from django.contrib import messages
from ecommerce.models import Product,Profile
import datetime


def checkout(request):
    #get the cart
    cart=Cart(request)
    cart_products=cart.get_prods
    quantities=cart.get_quants
    totals= cart.cart_total()
    sum=cart.total()
    # Generate unique pid using timestamp
    pid = f"{request.user.id}_{int(time.time())}" if request.user.is_authenticated else f"GUEST_{int(time.time())}"
    
    if request.user.is_authenticated:
        try:
            # Try to fetch the current user's shipping info
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


def billing_info(request):
    if request.POST:
        #get the cart
        cart=Cart(request)
        cart_products=cart.get_prods
        quantities=cart.get_quants
        totals= cart.cart_total()

        #create a session with shipping info
        my_shipping=request.POST
        request.session['my_shipping']=my_shipping

        #check to see if user is logged in
        if request.user.is_authenticated:
            #get the billing form
            billing_form=PaymentForm()
            return render(request, "payment/billing_info.html", {"cart_products": cart_products,"quantities":quantities,"totals":totals,"sum":sum,"shipping_info":request.POST,"billing_form":billing_form})
        else:
            #not logged in
            messages.success(request,"User must be logged in to continue billing!!")
            return redirect('home')
    
    else:
        messages.success(request,"Access Denied")
        return redirect('checkout')

def process_order(request):
    if request.POST:
        #get the cart
        cart=Cart(request)
        cart_products=cart.get_prods
        quantities=cart.get_quants
        totals= cart.cart_total()

        #get billing info from last page
        payment_form=PaymentForm(request.POST or None)
        #get shipping session data
        my_shipping=request.session.get('my_shipping')
        #gather order in
        full_name=my_shipping['shipping_full_name']
        email=my_shipping['shipping_email']
        #create shipping address from session info
        shipping_address=f"{ my_shipping['shipping_address1']}\n{ my_shipping['shipping_city']}\n{ my_shipping['shipping_province']}\n{ my_shipping['shipping_zipcode']}\n{ my_shipping['shipping_country']}"
        amount_paid=totals 

        if request.user.is_authenticated:
            #logged in
            user=request.user
            #create order
            create_order=Order(user=user,full_name=full_name,email=email,shipping_address=shipping_address,amount_paid=amount_paid)
            create_order.save()

            #add order items
            #get order ID
            order_id=create_order.pk
            #get product info
            for product in cart_products():
                #get product id
                product_id=product.id
                #get product price
                if product.is_sale:
                    price=product.sale_price
                else:
                    price=product.price

                #get quantity
                for key,value in quantities().items():
                    if int(key) ==product.id:
                        #Create order item
                        create_order_item=OrderItem(order_id=order_id,product_id=product_id,user=user,quantity=value,price=price)
                        create_order_item.save()
            
            #Delete our cart
            for key in list(request.session.keys()):
                if key=="session_key":
                    #Delete the key
                    del request.session[key]

            #delete cart from database(old cart field)
            current_user=Profile.objects.filter(user_id=request.user.id)
            #delete shopping cartin database(old cart field)
            current_user.update(old_cart="")


            messages.success(request,"Order Placed!!")
            return redirect('home')

        else:
            #not logged in 
            pass
        
    else:
        messages.success(request,"Access Denied")
        return redirect('checkout')

def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders=Order.objects.filter(shipped=True)
        if request.POST:
            status=request.POST['shipping_status']
            num=request.POST['num']
            #get the order
            order=Order.objects.filter(id=num)
            #grab date & time
            now=datetime.datetime.now()
            #update order
            order.update(shipped=False)
            #redirect
            messages.success(request,"Shipping status Updated!!!")
            return redirect('home')
        return render(request, "payment/shipped_dash.html", {"orders":orders})
    else:
        messages.success(request,"Access Denied")
        return redirect('home')


def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders=Order.objects.filter(shipped=False)
        if request.POST:
            status=request.POST['shipping_status']
            num=request.POST['num']
            #get the order
            order=Order.objects.filter(id=num)
            #grab date & time
            now=datetime.datetime.now()
            #update order
            order.update(shipped=True,date_shipped=now)
            #redirect
            messages.success(request,"Shipping status Updated!!!")
            return redirect('home')
        return render(request, "payment/not_shipped_dash.html", {"orders":orders})
    else:
        messages.success(request,"Access Denied")
        return redirect('home')
    

def orders(request,pk):
    if request.user.is_authenticated and request.user.is_superuser:
        #get the order
        order=Order.objects.get(id=pk)
        #get the order items
        items=OrderItem.objects.filter(order=pk)

        if request.POST:
            status=request.POST['shipping_status']
            #check if true or false
            if status=="true":
                #get order
                order=Order.objects.filter(id=pk)
                #update the status
                now=datetime.datetime.now()
                order.update(shipped=True,date_shipped=now)
            else:
                 #get order
                order=Order.objects.filter(id=pk)
                #update the status
                order.update(shipped=False)

            messages.success(request,"Shipping status Updated!!!")
            return redirect('home')

        return render(request, "payment/orders.html", {"order":order,"items":items})
    else:
        messages.success(request,"Access Denied")
        return redirect('home')


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
    #delete the browser cart
    #first Get the cart
    #get the cart
    cart=Cart(request)
    totals= cart.cart_total()
    
    # Clear the session cart
    cart_keys = [key for key in request.session.keys() if key.startswith('cart')]
    for key in list(request.session.keys()):
        if key=="session_key":
            #Delete the key
            del request.session[key]
    # Render the success page with total amounts
    return render(request, "payment/payment_success.html", {"totals": totals})

    # #Delete our cart
    # for key in list(request.session.keys()):
    #         if key=="session_key":
    #         #Delete the key
    #             del request.session[key]
            


def payment_failed(request):
    return render(request, "payment/payment_failed.html", {})

        

    

