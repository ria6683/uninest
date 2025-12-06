
import os


# 1. UPDATE SETTINGS.PY (Configure Gmail)

# Note: We append this to the end of the file

settings_additions = """

# EMAIL CONFIGURATION

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'roomease00@gmail.com'

EMAIL_HOST_PASSWORD = 'wqpo poxa hayf ybfh'  # <--- REPLACE THIS

"""


with open('melbourne_rentals/settings.py', 'a') as f:

    f.write(settings_additions)


# 2. UPDATE URLS.PY (Add Password Reset Routes)

urls_code = """

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

"""


with open('core/urls.py', 'w') as f:

    f.write(urls_code)


# 3. UPDATE VIEWS.PY (Send Email on Chat Message)

views_code = """

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required, user_passes_test

from django.contrib.auth import login

from django.core.paginator import Paginator

from django.core.mail import send_mail

from django.db.models import Q

from django.conf import settings

import stripe

from .models import Room, Inquiry, Message, Profile

from .forms import RoomForm, MessageForm, RegisterForm


stripe.api_key = settings.STRIPE_SECRET_KEY


def is_staff_check(user):

    return user.is_staff


def home(request):

    latest_rooms = Room.objects.order_by('-created_at')[:3]

    return render(request, 'core/home.html', {'latest_rooms': latest_rooms})


def room_list(request):

    query = request.GET.get('q', '')

    min_price = request.GET.get('min_price')

    max_price = request.GET.get('max_price')

    room_type = request.GET.get('room_type')

    rooms = Room.objects.all()


    if query:

        rooms = rooms.filter(Q(suburb__icontains=query) | Q(title__icontains=query))

    if min_price:

        rooms = rooms.filter(price_per_week__gte=min_price)

    if max_price:

        rooms = rooms.filter(price_per_week__lte=max_price)

    if room_type:

        rooms = rooms.filter(room_type=room_type)

    

    paginator = Paginator(rooms.order_by('-created_at'), 9)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)


    return render(request, 'core/room_list.html', {'page_obj': page_obj, 'values': request.GET})


def room_detail(request, pk):

    room = get_object_or_404(Room, pk=pk)

    return render(request, 'core/room_detail.html', {'room': room})


@login_required

def start_chat(request, room_id):

    room = get_object_or_404(Room, pk=room_id)

    if room.owner == request.user:

        return redirect('dashboard')

    inquiry, created = Inquiry.objects.get_or_create(

        room=room,

        sender=request.user,

        recipient=room.owner

    )

    return redirect('chat_detail', pk=inquiry.pk)


@login_required

def chat_detail(request, pk):

    inquiry = get_object_or_404(Inquiry, pk=pk)

    if request.user != inquiry.sender and request.user != inquiry.recipient:

        return redirect('dashboard')

        

    messages = inquiry.messages.order_by('created_at')

    

    if request.method == 'POST':

        form = MessageForm(request.POST)

        if form.is_valid():

            msg = form.save(commit=False)

            msg.inquiry = inquiry

            msg.sender = request.user

            msg.save()

            

            # --- EMAIL NOTIFICATION LOGIC ---

            # Send email to roomease00@gmail.com

            subject = f"New Chat Message from {request.user.username}"

            body = f"User: {request.user.username}\nRoom: {inquiry.room.title}\n\nMessage:\n{msg.text}"

            try:

                send_mail(

                    subject, 

                    body, 

                    settings.EMAIL_HOST_USER, 

                    ['roomease00@gmail.com'], 

                    fail_silently=True

                )

            except:

                pass # Don't crash if email fails

            # -------------------------------


            return redirect('chat_detail', pk=pk)

    else:

        form = MessageForm()

        

    return render(request, 'core/chat.html', {'inquiry': inquiry, 'messages': messages, 'form': form})


def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            ref_code = form.cleaned_data.get('referral_code')

            if ref_code:

                try:

                    referrer_profile = Profile.objects.get(referral_code=ref_code)

                    user.profile.referred_by = referrer_profile.user

                    user.profile.save()

                except Profile.DoesNotExist:

                    pass

            login(request, user)

            return redirect('dashboard')

    else:

        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required

def dashboard(request):

    user_rooms = Room.objects.filter(owner=request.user).order_by('-created_at')

    my_chats = Inquiry.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('-created_at')

    return render(request, 'core/dashboard.html', {'rooms': user_rooms, 'chats': my_chats})


@login_required

@user_passes_test(is_staff_check, login_url='/dashboard/')

def create_room(request):

    if request.method == 'POST':

        form = RoomForm(request.POST, request.FILES)

        if form.is_valid():

            room = form.save(commit=False)

            room.owner = request.user

            room.save()

            return redirect('dashboard')

    else:

        form = RoomForm()

    return render(request, 'core/room_form.html', {'form': form, 'title': 'Add New Room'})


@login_required

@user_passes_test(is_staff_check, login_url='/dashboard/')

def edit_room(request, pk):

    room = get_object_or_404(Room, pk=pk, owner=request.user)

    if request.method == 'POST':

        form = RoomForm(request.POST, request.FILES, instance=room)

        if form.is_valid():

            form.save()

            return redirect('dashboard')

    else:

        form = RoomForm(instance=room)

    return render(request, 'core/room_form.html', {'form': form, 'title': 'Edit Room'})


@login_required

@user_passes_test(is_staff_check, login_url='/dashboard/')

def delete_room(request, pk):

    room = get_object_or_404(Room, pk=pk, owner=request.user)

    if request.method == 'POST':

        room.delete()

        return redirect('dashboard')

    return render(request, 'core/room_confirm_delete.html', {'room': room})


def create_checkout_session(request, pk):

    room = get_object_or_404(Room, pk=pk)

    price_cents = int(room.price_per_week * 100)

    if request.is_secure():

        protocol = 'https://'

    else:

        protocol = 'http://'

    host = request.get_host()

    session = stripe.checkout.Session.create(

        payment_method_types=['card'],

        line_items=[{

            'price_data': {

                'currency': 'aud',

                'product_data': {

                    'name': f"Bond Payment: {room.title}",

                    'description': f"1 week rent for {room.suburb} property.",

                },

                'unit_amount': price_cents,

            },

            'quantity': 1,

        }],

        mode='payment',

        success_url=f"{protocol}{host}/payment_success/",

        cancel_url=f"{protocol}{host}/rooms/{pk}/",

    )

    return redirect(session.url, code=303)


def payment_success(request):

    return render(request, 'core/success.html')

"""


with open('core/views.py', 'w') as f:

    f.write(views_code)


# 4. CREATE PASSWORD RESET TEMPLATES

# Form to request reset

reset_form_html = """{% extends 'base.html' %}

{% block content %}

<div class="container py-5 text-center" style="max-width: 500px;">

    <h3>Reset Password</h3>

    <p>Enter your email address and we'll send you a link to reset your password.</p>

    <form method="post">

        {% csrf_token %}

        <div class="mb-3">{{ form.email.label_tag }} {{ form.email }}</div>

        <button type="submit" class="btn btn-primary w-100">Send Reset Link</button>

    </form>

</div>

<script>

    // Add bootstrap class to input

    document.querySelector('input[type="email"]').classList.add('form-control');

</script>

{% endblock %}"""


# Email sent confirmation

reset_done_html = """{% extends 'base.html' %}

{% block content %}

<div class="container py-5 text-center">

    <h3>Check your inbox!</h3>

    <p>We've emailed you instructions for setting your password.</p>

    <p>If you don't receive an email, please check your spam folder.</p>

</div>

{% endblock %}"""


# Form to enter new password

reset_confirm_html = """{% extends 'base.html' %}

{% block content %}

<div class="container py-5" style="max-width: 500px;">

    <h3 class="text-center">Set New Password</h3>

    <form method="post">

        {% csrf_token %}

        {{ form.as_p }}

        <button type="submit" class="btn btn-success w-100 mt-3">Change Password</button>

    </form>

</div>

{% endblock %}"""


# Success page

reset_complete_html = """{% extends 'base.html' %}

{% block content %}

<div class="container py-5 text-center">

    <h3 class="text-success">Password Changed!</h3>

    <p>Your password has been set. You may go ahead and log in now.</p>

    <a href="/accounts/login/" class="btn btn-primary">Log In</a>

</div>

{% endblock %}"""


# Add "Forgot Password?" link to Login page

login_html = """{% extends 'base.html' %}

{% block content %}

<div class="container py-5" style="max-width:400px;">

    <h2>Login</h2>

    <form method="post">

        {% csrf_token %}

        {{ form.as_p }}

        <button class="btn btn-primary w-100">Login</button>

    </form>

    <div class="mt-3 text-center">

        <a href="{% url 'password_reset' %}" class="text-muted small">Forgot Password?</a>

    </div>

</div>

{% endblock %}"""


with open('templates/registration/password_reset_form.html', 'w') as f:

    f.write(reset_form_html)

with open('templates/registration/password_reset_done.html', 'w') as f:

    f.write(reset_done_html)

with open('templates/registration/password_reset_confirm.html', 'w') as f:

    f.write(reset_confirm_html)

with open('templates/registration/password_reset_complete.html', 'w') as f:

    f.write(reset_complete_html)

with open('templates/registration/login.html', 'w') as f:

    f.write(login_html)


print("✅ Email & Password Reset configured!")

