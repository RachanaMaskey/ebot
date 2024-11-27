from django.urls import path, include 
from .import views

urlpatterns = [
    path('',views.home,name='home'),
    path('about/',views.about,name='about'),
    path('contact/',views.contact,name='contact'),
    path('login/',views.login_user,name='login'),
    path('logout/',views.logout_user,name='logout'),
    path('register/',views.register_user,name='register'),
    path('allproduct/',views.allproduct,name='allproduct'),
    path('product/<int:pk>',views.product,name='product'),
    path('category/<str:cat>',views.category,name='category'),
    path('category_summary/',views.category_summary,name='category_summary'),


#for chatbot
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chat/', views.chatbot_page, name='chatbot_page'),

    #for chat history
    path('get-chat-history/', views.get_chat_history, name='get_chat_history'),
    path('save-chat-history/', views.save_chat_history, name='save_chat_history'),
    

    #for result analysis
    path('result-analysis/', views.chatbot_workflow_analysis, name='result_analysis'),
    path('store-query/', views.store_query, name='store_query'),

    
]