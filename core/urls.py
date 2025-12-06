

from django.urls import path, include

from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

    # Standard Views

    path('', views.home, name='home'),

    path('rooms/', views.room_list, name='room_list'),

    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),

    

    # Chat & Payments

    path('rooms/<int:room_id>/chat/', views.start_chat, name='start_chat'),

    path('chat/<int:pk>/', views.chat_detail, name='chat_detail'),

    path('rooms/<int:pk>/checkout/', views.create_checkout_session, name='create_checkout_session'),

    path('payment_success/', views.payment_success, name='payment_success'),

    

    # Auth & Dashboard

    path('register/', views.register, name='register'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('dashboard/create/', views.create_room, name='create_room'),

    path('dashboard/edit/<int:pk>/', views.edit_room, name='edit_room'),

    path('dashboard/delete/<int:pk>/', views.delete_room, name='delete_room'),

    

    # PASSWORD RESET URLS (Built-in Django Magic)

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),

    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

]

