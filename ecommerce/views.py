from django.shortcuts import render,redirect
from .models import Product,Category,Profile
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import SignUpForm,UpdateUserForm,ChangePasswordForm,UserInfoForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django.core.paginator import Paginator
import json
from cart.cart import Cart

def home(request):
    # Fetch all sale products
    sale_products = Product.objects.filter(is_sale=True)
    # Fetch featured products excluding those already in sale
    products = Product.objects.filter(is_sale=False).order_by('?')[:4]
    return render(request, 'home.html', {
        'sale_products': sale_products,
        'products': products
    })

def about(request):
    return render(request,'about.html',{})

def contact(request):
    return render(request,'contact.html',{})


def allproduct(request):
    query = request.GET.get('q', '')  
    products = Product.objects.all()  # Fetch all products initially
    categories = Category.objects.all()
    no_products_found = False  # Flag to track if no products are found

    if query:
        search_query = query.replace(' ', '_')
        products = products.filter(name__icontains=search_query) | products.filter(category__name__iexact=query)

    # Check if any products are available after filtering
    if not products.exists():
        no_products_found = True

    # Add pagination
    paginator = Paginator(products, 4) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': products,
        'page_obj': page_obj,
        'original_query': query,  # Pass the search query back to the template
        'no_products_found': no_products_found,  # Include the flag in the context
    }
    return render(request, 'allproduct.html', context)



def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Check if username or password fields are empty
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return redirect('login')

        # Check if the username exists
        if not User.objects.filter(username=username).exists():
            messages.error(request, "The username you entered does not exist.")
            return redirect('login')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            #Do some shopping cart stuff
            current_user=Profile.objects.get(user__id=request.user.id)

            #get their saved cart from database
            saved_cart=current_user.old_cart
            
            #convert database string to python dictionary
            if saved_cart:
                #convert to dictionary using JSON
                converted_cart=json.loads(saved_cart)
                #add the loaded cart dictionary to our session
                #get the cart
                cart=Cart(request)
                #loop through the cart and add items from the database
                for key,value in converted_cart.items():
                    cart.db_add(product=key,quantity=value)

            messages.success(request, "You have logged in successfully!")
            return redirect('home')
        else:
            messages.error(request, "Invalid password. Please try again.")
            return redirect('login')
    else:
        return render(request, 'login.html', {})

def logout_user(request):
    # Clear chat history from session
    if 'chat_history' in request.session:
        del request.session['chat_history']
    
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            # Log in user
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have registered successfully!")
            return redirect('update_info')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect('register')
    else:
        return render(request, 'register.html', {'form': form})

def product(request,pk):
    product= Product.objects.get(id=pk)
    return render(request,'product.html',{'product':product})

def category(request,cat):
    #replace hyphens with spaces
    cat=cat.replace('_',' ')
    #grab the category from url
    try:
        #look up the category
        category=Category.objects.get(name=cat)
        products=Product.objects.filter(category=category)
        return render(request,'category.html',{'products':products,'category':category})

    except:
        messages.success(request,("The category doesn't exist..."))
        return redirect('home')
    
def category_summary(request):
    products= Product.objects.all()
    categories=Category.objects.all()
    return render(request,'category_summary.html',{"categories":categories,"products":products})    

def update_user(request):
    if request.user.is_authenticated:
        current_user=User.objects.get(id=request.user.id)
        user_form= UpdateUserForm(request.POST or None, instance=current_user)

        if user_form.is_valid():
            user_form.save()

            login(request,current_user)
            messages.success(request,"User profile has been updated!!!")
            return redirect('home')
        else:
            for error in list(user_form.errors.values()):
                    messages.error(request,error)
        return render(request,"update_user.html",{'user_form':user_form})
    else:
        messages.success(request,"User must be logged in")
        return redirect('home')
    

def update_password(request):
    if request.user.is_authenticated:
        current_user=request.user
        #did they fill out the form
        if request.method == 'POST':
            form=ChangePasswordForm(current_user,request.POST)
            #is the form valid
            if form.is_valid():
                form.save()
                messages.success(request,"Your password has been updated!!!!!!!!")
                login(request,current_user)
                return redirect('update_user')
            
            else:
                for error in list(form.errors.values()):
                    messages.error(request,error)
                    return redirect('update_password')

        else:
            form=ChangePasswordForm(current_user)
            return render(request,"update_password.html",{'form':form})
        
    else:
        messages.success(request,"User must be logged in")
        return redirect('home')
    

def update_info(request):
    if request.user.is_authenticated:
        #get currnet user
        current_user=Profile.objects.get(user__id=request.user.id)
        #get current users shipping info
        shipping_user=ShippingAddress.objects.get(user__id=request.user.id)
        #get original user form
        form= UserInfoForm(request.POST or None, instance=current_user)
        #get users shipping form
        shipping_form=ShippingForm(request.POST or None, instance=shipping_user)

        if form.is_valid() or shipping_form.is_valid():
            #save original form
            form.save()
            #save shipping form
            shipping_form.save()
            messages.success(request,"Your informations has been updated!!!")
            return redirect('home')
        else:
            for error in list(form.errors.values()):
                    messages.error(request,error)
        return render(request,"update_info.html",{'form':form,'shipping_form':shipping_form})
    else:
        messages.success(request,"User must be logged in")
        return redirect('home')
        



# for the chatbot

from django.http import JsonResponse
from .naive_bayes_chatbot import generate_response  

def chatbot_view(request):
    user_message = request.GET.get('message', '')  
    chat_history = request.session.get('chat_history', [])  # Get chat history from the session
    
    if user_message:
        bot_response = generate_response(user_message, request)  
       
        chat_history.append({'user': user_message, 'bot': bot_response})
        request.session['chat_history'] = chat_history  # Update session with new history
    else:
        bot_response = "Please enter a message"

    return JsonResponse({'response': bot_response, 'history': chat_history})  # Return JSON response to the frontend


def chatbot_page(request):
    context={}
    return render(request, 'chatbot.html',context)


# for chat history

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .models import ChatHistory

@login_required
def get_chat_history(request):
    try:
        history = ChatHistory.objects.get(user=request.user)
        return JsonResponse({'status': 'success', 'history': history.history}, safe=False)
    except ChatHistory.DoesNotExist:
        return JsonResponse({'status': 'success', 'history': ''}, safe=False)

@csrf_exempt
@login_required
def save_chat_history(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        history, created = ChatHistory.objects.get_or_create(user=request.user)
        history.history = data.get('history', '')
        history.save()
        return JsonResponse({'status': 'success'})





#for resukt analysis
from .naive_bayes_chatbot import preprocess_text, classify_intent, train_naive_bayes, generate_response,extract_product_names,get_product_details,extract_category_name,get_products_in_category
import json,os,math

def store_query(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get("query", "").strip()

        if user_query:
            # Save the query to the session for analysis
            request.session["current_query"] = user_query
            print(f"Stored query in session: {user_query}")  # Debugging line

            return JsonResponse({"status": "success", "message": "Query saved for analysis."})
        else:
            return JsonResponse({"status": "error", "message": "Query is empty."})

    return JsonResponse({"status": "error", "message": "Invalid request method."})


import math

# Levenshtein Distance function
def levenshtein_distance(str1, str2):
    """
    Calculate the Levenshtein distance between two strings.
    """
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0:
                dp[i][j] = j
            elif j == 0:
                dp[i][j] = i
            elif str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[m][n]


def chatbot_workflow_analysis(request):
    # Retrieve the current user query from the session
    user_query = request.session.get("current_query", None)
    
    # If no query is found in the session, provide a fallback query for demo purposes
    if not user_query:
        user_query = ""
    
    # Load intents
    json_file_path = os.path.join(os.path.dirname(__file__), 'data', 'intents.json')
    with open(json_file_path, 'r') as file:
        intents = json.load(file)["intents"]
    
    # Train Naive Bayes
    word_counts, intent_counts, total_words, vocab_size = train_naive_bayes(intents)
    
    # Preprocessing
    preprocessed_tokens = preprocess_text(user_query)
    
    # Classify intent
    intent_probabilities = {}
    best_intent = None
    max_prob = -float('inf')
    
    # Calculate the raw log probabilities
    for intent, count in intent_counts.items():
        log_prob = math.log(count / sum(intent_counts.values()))
        for word in preprocessed_tokens:
            word_prob = (word_counts[intent][word] + 1) / (sum(word_counts[intent].values()) + vocab_size)
            log_prob += math.log(word_prob)
        
        # Convert log probability to actual probability
        prob = math.exp(log_prob)
        intent_probabilities[intent] = prob
    
    # Normalize the probabilities (scale them to sum to 1)
    total_prob = sum(intent_probabilities.values())
    if total_prob > 0:
        for intent in intent_probabilities:
            intent_probabilities[intent] = (intent_probabilities[intent] / total_prob) * 100  # Convert to percentage
    
    # Find the best intent
    best_intent = max(intent_probabilities, key=intent_probabilities.get)
    
    # Generate response data
    response_data = {
        "product_name": None,
        "category_name": None,
        "product_response": None,
        "category_response": None,
        "levenshtein_distances": {}  # Store Levenshtein distances for categories
    }
    
    if best_intent == "product_search":
        product_names = extract_product_names(user_query)
        
        # If it's a list, take the first product name (or handle it accordingly)
        if isinstance(product_names, list) and len(product_names) > 0:
            product_name = product_names[0]  # Get the first product name from the list
        else:
            product_name = product_names  # If it's already a string, use it directly
        
        product_name = product_name.replace("_", " ")    
        response_data["product_name"] = product_name
        
        # Get product details using the cleaned product name
        response_data["product_response"] = get_product_details(product_name)

    elif best_intent == "category_search":
        response_data["category_name"] = extract_category_name(user_query)
        response_data["category_response"] = get_products_in_category(response_data["category_name"])
        
        # Calculate Levenshtein distance for category search
        categories = ["earring", "watch", "ring", "sunglasses", "necklace", "bracelet"]  # Modify this as per your categories
        user_input = user_query.lower()
        distances = {}
        
        for category in categories:
            distance = levenshtein_distance(user_input, category)
            distances[category] = distance
        
        response_data["levenshtein_distances"] = distances
    
    # Final response generation
    response = generate_response(user_query,request)
    
    # Pass data to template
    context = {
        "user_query": user_query,
        "preprocessed_tokens": preprocessed_tokens,
        "intent_probabilities": {k: round(v, 2) for k, v in intent_probabilities.items()},  # Rounded to two decimals
        "best_intent": best_intent,
        "response": response,
        **response_data
    }
    
    return render(request, "resultanalysis.html", context)
