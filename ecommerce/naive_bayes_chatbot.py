import json
import re
import os
import math
from collections import defaultdict, Counter
import random

from cart.cart import Cart

from .models import Product
from .models import Category  

import json
import os

def save_user_input_and_intent(user_input, intent):
    new_file_path = os.path.join(os.path.dirname(__file__), 'data', 'user_input_intent.json')

    # Check if the file exists and if it contains valid JSON
    if os.path.exists(new_file_path):
        try:
            with open(new_file_path, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            # If the file is empty or invalid, initialize with an empty structure
            data = {"intents": []}
    else:
        data = {"intents": []}  # Initialize with an empty list if the file doesn't exist

    # Append the new user input, intent, and bot response as a pattern
    data["intents"].append({
        "patterns": user_input,
        "tag": intent,
    })
    # Write the updated data back to the file
    with open(new_file_path, 'w') as file:
        json.dump(data, file, indent=4)

json_file_path = os.path.join(os.path.dirname(__file__), 'data', 'intents.json')

STOPWORDS = {"the", "is","are", "and", "any", "in", "to", "a", "of", "for", "on", "it", "with", "me"}
SUFFIXES = []

def preprocess_text(text):
    text = text.lower()
    text = ''.join([char if char.isalnum() or char.isspace() else '' for char in text])
    tokens = text.split()
    # Remove stopwords and stem words
    return [stem_word(word) for word in tokens if word not in STOPWORDS]

def stem_word(word):
    for suffix in SUFFIXES:
        if word.endswith(suffix):
            return word[:-len(suffix)]
    return word

#for handling typos
def levenshtein_distance(str1, str2):
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

def train_naive_bayes_with_user_data():
    # Load intents from both files
    with open(json_file_path, 'r') as file:
        intents = json.load(file)["intents"]
    
    user_file_path = os.path.join(os.path.dirname(__file__), 'data', 'user_input_intent.json')
    with open(user_file_path, 'r') as file:
        user_data = json.load(file)["intents"]
    
    # Add user input patterns to intents
    for user_input in user_data:
        # Ensure patterns are a list
        patterns = [user_input["patterns"]] if isinstance(user_input["patterns"], str) else user_input["patterns"]
        intents.append({"tag": user_input["tag"], "patterns": patterns})
    
    return train_naive_bayes(intents)

def train_naive_bayes(intents):
    word_counts = defaultdict(Counter)
    intent_counts = Counter()
    total_words = 0
    vocabulary = set()

    for intent in intents:
        tag = intent['tag']
        for pattern in intent['patterns']:
            words = preprocess_text(pattern)
            word_counts[tag].update(words)
            intent_counts[tag] += 1
            total_words += len(words)
            vocabulary.update(words)

    vocab_size = len(vocabulary)
    return word_counts, intent_counts, total_words, vocab_size

def classify_intent(user_input, word_counts, intent_counts, total_words, vocab_size):
    words = preprocess_text(user_input)
    best_intent = None
    max_prob = -float('inf')

    for intent, count in intent_counts.items():
        log_prob = math.log(count / sum(intent_counts.values()))  # Prior probability

        for word in words:
            word_prob = (word_counts[intent][word] + 1) / (sum(word_counts[intent].values()) + vocab_size)
            log_prob += math.log(word_prob)

        if log_prob > max_prob:
            max_prob = log_prob
            best_intent = intent

    return best_intent

def generate_response(user_input,request):
    with open(json_file_path, 'r') as file:
        intents = json.load(file)["intents"]

    word_counts, intent_counts, total_words, vocab_size = train_naive_bayes(intents)
    intent = classify_intent(user_input, word_counts, intent_counts, total_words, vocab_size)
    print(f"Detected intent: {intent}")

    # Save the user input and detected intent to the new JSON file
    save_user_input_and_intent(user_input, intent)

    # Response based on detected intent
    if intent == "product_search":
        product_names = extract_product_names(user_input)
        response = ""
        for product_name in product_names:
            product_details = get_product_details(product_name)
            response += product_details + "<br>"

        return response if response else "Sorry, I couldn't find any products you're asking about."

    elif intent == "category_search":
        category_name = extract_category_name(user_input)
        if category_name:
            return get_products_in_category(category_name)
        else:
            return "Sorry, we don’t have products in the category you're asking about."

    elif intent == "order_status":
        return "Please provide your order ID, and I’ll check the status for you."

    elif intent == "return_policy":
        return "You can return any product within 30 days of purchase. Visit our returns page for more details."

    elif intent == "payment_inquiry":
        payment_keywords = {
            "online payment": "We accept online payment in eSewa.",
            "esewa": "Yes, We accept online payment in eSewa.",
            "cash": "Yes, We accept cash on delivery as well.",
            "card": "Sorry, We currently donot have a system to accept cards.We can do esewa."
        }
        for keyword, response in payment_keywords.items():
            if keyword in user_input.lower():
                return response
            
        payment_keywords_na = {
            "paypal": "Sorry,we only accept online payment in eSewa.",
            "khalti": "Sorry,we only accept online payment in eSewa.",
            "visa": "Sorry,we only accept online payment in eSewa.",
            "venmo": "Sorry,we only accept online payment in eSewa.",
            "imepay": "Sorry,we only accept online payment in eSewa.",
            
        }
        for keyword, response in payment_keywords_na.items():
            if keyword in user_input.lower():
                return response
        return "We accept both cash on delivery or eSewa payment if online payment is preferred."


    elif intent == "shipping_inquiry":
        return "Shipping usually takes 5-7 business days. You can track your order on our tracking page."

    elif intent == "customer_service":
        customer_service_faqs = {
            "refund": "Refunds are processed within 5-7 business days after receiving the returned product.",
            "cancel order": "To cancel an order, go to your orders page and click on the cancel button for the relevant order.",
            "track order": "You can track your order on our tracking page using the order ID sent to your email.",
            "complaint": "We are sorry to hear about your complaint. Please provide details, and we will resolve it promptly.",
            "damaged product": "If you received a damaged product, please contact our support team with a photo of the product.",
            "exchange": "You can exchange products within 15 days of delivery. Visit the exchanges page for more details.",
            "contact support": "You can contact our support team at glimmerservice@mail.com or call +977 9841123456.",
            "hours": "Our support team is available from 9 AM to 6 PM, Monday to Saturday."
        }

        for keyword, response in customer_service_faqs.items():
            if keyword in user_input.lower():
                return response
        return "You can contact our support team at glimmerservice@mail.com or call +977 9841123456."

    elif intent == "feedback":
        return "You can leave feedback on the product page or through our contact page."

    elif intent == "greeting":
        return random.choice([res["responses"] for res in intents if res["tag"] == "greeting"][0])

    elif intent == "farewell":
        return random.choice([res["responses"] for res in intents if res["tag"] == "farewell"][0])
    
    elif intent == "category_query":
        categories = Category.objects.values_list('name', flat=True) 
        if categories.exists():
            category_list = "<br>".join([
                f"<a href='{reverse('category', args=[category.replace(' ', '_')])}'><strong>{category}</strong></a>"
                for category in categories
            ])
            return f"Here are the categories available in our store:<br>{category_list}"
        else:
            return "Sorry, no categories are currently available in our store."

    elif intent == "help":
        return random.choice([res["responses"] for res in intents if res["tag"] == "help"][0])
    
    elif intent == "account_login":
        return 'To log in, click <a href="/login/">here</a> to access your account.'

    elif intent == "account_registration":
        return 'To register, click <a href="/signup/">here</a> to create an account.'
    
    elif intent == "view_cart":
        cart = Cart(request)  # Create a cart object using the current request session
        cart_products = cart.get_prods()  # Call the method to get the products in the cart
        quantities = cart.get_quants()  # Call the method to get the quantities for each product
        totals = cart.cart_total()  # Get the total prices for each product
        total_price = cart.total()  # Get the grand total price
        
        # Check if the cart is empty
        if not cart_products:  # If cart_products is empty
            response = "Your cart is empty. <a href='/allproduct/'>Browse our products</a>."
        else:
            # Create a response string with product names, quantities, and totals
            response = "Your cart contains: <br>"
            for product, quantity in zip(cart_products, quantities):
                response += f"<strong>Product:</strong> {product.name.replace('_',' ')}<br>"
                
                response += f"<strong>Price:</strong>Rs. {product.price} <br>"

            response += f"<strong><u>Total Price:</u></strong>Rs. {totals} <br>"

        return response


    elif intent == "add_to_cart":
        product_quantities = extract_product_quantities(user_input)  # Extract product names and quantities
        response = ""
        cart = Cart(request)  # Initialize the cart for the session

        for product_name, quantity in product_quantities.items():
            try:
                # Normalize product name for database lookup
                product = Product.objects.get(name__iexact=product_name.replace(" ", "_"))
                cart.add(product=product, quantity=quantity)  # Add the specified quantity
                response += f"Successfully added <strong>{quantity} x {product.name.replace('_', ' ')}</strong> to your cart.<br>"
            except Product.DoesNotExist:
                response += f"Sorry, we couldn't find a product named <strong>'{product_name.replace('_', ' ')}'</strong>.<br>"

        return response if response else "Please specify a valid product and quantity to add to your cart."

       
    

    return "I'm not sure how to respond to that."


def extract_product_names(user_input):
    words = preprocess_text(user_input.lower())
    keywords = ["about", "product", "item", "is", "want", "show", "tell", "have", "details", "info","buy"
                ,"add", "put", "place"]
    product_names = []

    for keyword in keywords:
        if keyword in words:
            keyword_index = words.index(keyword)
            product_name_start_index = keyword_index + 1

            if product_name_start_index < len(words):
                extracted_words = words[product_name_start_index:]

                for i in range(len(extracted_words)):
                    potential_name = "_".join(extracted_words[:i + 1]).capitalize()
                    
                    # Check against the actual product name
                    product = Product.objects.filter(name=potential_name).first()
                    if product:
                        product_names.append(product.name)
                        break
                    
                    # Check against alternate names
                    products = Product.objects.all()
                    for prod in products:
                        alternate_names = prod.get_alternate_names()
                        # Compare both the potential name and alternate names
                        if potential_name.lower() in alternate_names:
                            product_names.append(prod.name)
                            break

            break

    # Fallback check for alternate names
    if not product_names:
        fallback_name = "_".join(words).capitalize()
        product = Product.objects.filter(name=fallback_name).first()
        if product:
            product_names.append(product.name)
        else:
            products = Product.objects.all()
            for prod in products:
                alternate_names = prod.get_alternate_names()
                if fallback_name.lower() in alternate_names:
                    product_names.append(prod.name)
                    break

    return product_names if product_names else [user_input.strip().replace(" ", "_").capitalize()]



from django.urls import reverse

def get_product_details(product_name):
    try:
        product = Product.objects.get(name__iexact=product_name.replace(" ", "_"))
        product.name = product.name.replace('_', " ")
        product_url = reverse('product', args=[product.pk])
        product_details = f"We have: <br> <a href='{product_url}'><strong>{product.name}</strong></a> : Rs.{product.price}.<br>"
        return product_details
    except Product.DoesNotExist:
        return f"Sorry, we couldn't find a product named <strong>'{product_name.replace('_',' ')}'</strong>."
    


def get_product_by_id(product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.name = product.name.replace('_', " ")
        product_details = f"We have <strong>{product.name}</strong> : Rs.{product.price}.<br>"
        return product_details
    except Product.DoesNotExist:
        return f"Sorry, we couldn't find a product with ID <strong>{product_id}</strong>."

def extract_category_name(user_input):
    categories = ["earring", "watch", "ring", "sunglasses", "necklace", "bracelet"]
    user_words = user_input.lower().split() 

    threshold = 2 
    best_match = None
    min_distance = float('inf')

    for word in user_words:
        for category in categories:
            distance = levenshtein_distance(word, category)
            
            if distance < min_distance and distance <= threshold:
                min_distance = distance
                best_match = category

    return best_match




def get_products_in_category(category_name):
    products = Product.objects.filter(category__name__iexact=category_name)
    if products.exists():
        product_details = f"Here are the available products in the <strong>'{category_name}'</strong> category:<br>"
        for product in products:
            product.name = product.name.replace('_', ' ')
            # Use the reverse function to dynamically generate the URL for each product's detail page
            product_url = reverse('product', args=[product.pk])
            
            product_details += f"<a href='{product_url}'><strong>{product.name}</strong></a> - Rs.{product.price}<br>"
        return product_details
    else:
        return f"Sorry, we couldn't find any products in the <strong>'{category_name}'</strong> category."



import re
def extract_product_quantities(user_input):
   
    pattern = r"(\d+)\s+([\w\s]+)(?:,|and|to the cart|$)"
    matches = re.findall(pattern, user_input, re.IGNORECASE)

    product_quantities = {}
    for match in matches:
        quantity, product_name = match
        product_name = product_name.strip().lower()  # Normalize product name
        product_quantities[product_name] = int(quantity)

    return product_quantities
