from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/chat/', views.start_chat, name='start_chat'),
    path('chat/<int:pk>/', views.chat_detail, name='chat_detail'),
    path('rooms/<int:pk>/checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/create/', views.create_room, name='create_room'),
    path('dashboard/edit/<int:pk>/', views.edit_room, name='edit_room'),
    path('dashboard/delete/<int:pk>/', views.delete_room, name='delete_room'),
]