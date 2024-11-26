import json
import re
import os
import math
from collections import defaultdict, Counter
import random
from .models import Product

json_file_path = os.path.join(os.path.dirname(__file__), 'data', 'intents.json')

STOPWORDS = {"the", "is","are", "and", "in", "to", "a", "of", "for", "on", "it", "with", "me"}
SUFFIXES = []

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    tokens = text.split()
    # Remove stopwords and stem words
    return [stem_word(word) for word in tokens if word not in STOPWORDS]

def stem_word(word):
    for suffix in SUFFIXES:
        if word.endswith(suffix):
            return word[:-len(suffix)]
    return word

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

def generate_response(user_input):
    with open(json_file_path, 'r') as file:
        intents = json.load(file)["intents"]

    word_counts, intent_counts, total_words, vocab_size = train_naive_bayes(intents)
    intent = classify_intent(user_input, word_counts, intent_counts, total_words, vocab_size)
    print(f"Detected intent: {intent}")

    # Response based on detected intent
    if intent == "product_search":
        product_name = extract_product_name(user_input)
        if product_name:
            return get_product_details(product_name)
        else:
            return "Sorry, I couldn't understand the product you're asking about."

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
            "esewa": "We accept online payment in eSewa.",
            "cash": "We accept cash on delivery as well.",
            "card": "We currently donot have a system to accept cards.We can do esewa."
        }
        for keyword, response in payment_keywords.items():
            if keyword in user_input.lower():
                return response

        # Default fallback response
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
            "work hour": "Our support team is available from 9 AM to 6 PM, Monday to Saturday."
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

    elif intent == "help":
        return "I’m here to help! Let me know what you need assistance with."

    return "I'm not sure how to respond to that."

def extract_product_name(user_input):
    words = preprocess_text(user_input)
    keywords = ["about", "product", "item", "is", "want", "show"]

    for keyword in keywords:
        if keyword in words:
            product_name_start_index = words.index(keyword) + 1
            if product_name_start_index < len(words):
                product_name = " ".join(words[product_name_start_index:]).strip()
                return product_name.replace(" ", "_").capitalize()
    return " ".join(words).strip().replace(" ", "_").capitalize()

def get_product_details(product_name):
    try:
        product = Product.objects.get(name__iexact=product_name.replace(" ", "_"))
        product.name = product.name.replace('_', " ")
        product_details = f"We have <strong>{product.name}</strong> : Rs.{product.price}.<br>"
        return product_details
    except Product.DoesNotExist:
        return f"Sorry, we couldn't find a product named <strong>'{product_name}'</strong>."

def extract_category_name(user_input):
    categories = ["earring", "watch", "ring", "sunglasses", "necklace", "bracelet"]
    user_input = user_input.lower()

    for category in categories:
        if category in user_input:
            return category
    return None

def get_products_in_category(category_name):
    products = Product.objects.filter(category__name__iexact=category_name)
    if products.exists():
        product_details = f"Here are the available products in the <strong>'{category_name}'</strong> category:<br>"
        for product in products:
            product.name = product.name.replace('_', ' ')
            product_details += f"<strong>{product.name}</strong> - Rs.{product.price}<br>"
        return product_details
    else:
        return f"Sorry, we couldn't find any products in the <strong>'{category_name}'</strong> category."
