import os

# 1. UPDATE MODELS (Add Chat Messages & User Profiles)
models_code = """
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Room(models.Model):
    ROOM_TYPES = [
        ('private', 'Private Room'),
        ('shared', 'Shared Room'),
        ('studio', 'Studio Apartment'),
        ('whole', 'Whole Property'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rooms')
    title = models.CharField(max_length=200)
    suburb = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='private')
    description = models.TextField()
    availability_date = models.DateField()
    inspection_time = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Saturday 10:00 AM - 11:00 AM")
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='room_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.suburb}"

# Inquiry acts as the "Chat Thread"
class Inquiry(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='inquiries')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_inquiries')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_inquiries')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.sender.username} -> {self.recipient.username}"

# Individual Messages in the thread
class Message(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.text[:20]}"

# Referral Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

# Auto-create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure profile exists for old users
        Profile.objects.get_or_create(user=instance)
"""

# 2. UPDATE FORMS (Add Message Form & Referral Code Field)
forms_code = """
from django import forms
from .models import Room, Message
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core import validators

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['title', 'suburb', 'address', 'price_per_week', 'room_type', 'availability_date', 'inspection_time', 'description', 'image']
        widgets = {
            'availability_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspection_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sat 10am - 11am'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type a message...'}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    referral_code = forms.CharField(required=False, help_text="Have a referral code? Enter it here.", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = "Enter a unique username. Spaces are allowed."
"""

# 3. UPDATE VIEWS (Chat Logic & Referral Logic)
views_code = """
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
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
        return redirect('dashboard') # Owners can't message themselves
        
    # Check if thread exists
    inquiry, created = Inquiry.objects.get_or_create(
        room=room,
        sender=request.user,
        recipient=room.owner
    )
    return redirect('chat_detail', pk=inquiry.pk)

@login_required
def chat_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    # Security: Ensure user is part of this chat
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
            return redirect('chat_detail', pk=pk)
    else:
        form = MessageForm()
        
    return render(request, 'core/chat.html', {'inquiry': inquiry, 'messages': messages, 'form': form})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Referral Logic
            ref_code = form.cleaned_data.get('referral_code')
            if ref_code:
                try:
                    referrer_profile = Profile.objects.get(referral_code=ref_code)
                    user.profile.referred_by = referrer_profile.user
                    user.profile.save()
                except Profile.DoesNotExist:
                    pass # Invalid code, ignore

            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # My Rooms (Admin only)
    user_rooms = Room.objects.filter(owner=request.user).order_by('-created_at')
    
    # Chats
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

# 4. URLS (Add Chat Routes)
urls_code = """
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
"""

# 5. CHAT HTML (The Chat Interface)
chat_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="card shadow-lg" style="max-height: 80vh;">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
                Chat regarding: <strong>{{ inquiry.room.title }}</strong>
            </h5>
            <a href="{% url 'dashboard' %}" class="btn btn-sm btn-light">Back to Dashboard</a>
        </div>
        
        <div class="card-body overflow-auto" id="chat-box" style="height: 500px; background: #f8f9fa;">
            {% for msg in messages %}
                <div class="d-flex {% if msg.sender == user %}justify-content-end{% else %}justify-content-start{% endif %} mb-3">
                    <div class="card p-3 shadow-sm {% if msg.sender == user %}bg-primary text-white{% else %}bg-white text-dark{% endif %}" style="max-width: 70%; border-radius: 15px;">
                        <small class="d-block {% if msg.sender == user %}text-light{% else %}text-muted{% endif %} mb-1" style="font-size: 0.75rem;">
                            {{ msg.sender.username }} • {{ msg.created_at|date:"D H:i" }}
                        </small>
                        {{ msg.text }}
                    </div>
                </div>
            {% empty %}
                <p class="text-center text-muted mt-5">No messages yet. Start the conversation!</p>
            {% endfor %}
        </div>

        <div class="card-footer bg-white">
            <form method="post" class="d-flex gap-2">
                {% csrf_token %}
                {{ form.text }}
                <button type="submit" class="btn btn-primary"><i class="bi bi-send-fill"></i></button>
            </form>
        </div>
    </div>
</div>

<script>
    // Auto-scroll to bottom of chat
    var chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Simple Auto-Reload every 5 seconds (Poor man's real-time chat)
    setTimeout(function(){
       location.reload(); 
    }, 5000);
</script>
{% endblock %}"""

# 6. DASHBOARD HTML (Show Referral Code & Chats)
dashboard_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    
    <div class="card bg-success text-white mb-4 shadow border-0">
        <div class="card-body d-flex justify-content-between align-items-center">
            <div>
                <h5 class="mb-0"><i class="bi bi-gift-fill"></i> Refer a Friend</h5>
                <p class="mb-0 small">Share this code with friends!</p>
            </div>
            <div class="bg-white text-success px-4 py-2 rounded fw-bold display-6">
                {{ user.profile.referral_code }}
            </div>
        </div>
    </div>

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="bi bi-speedometer2"></i> My Dashboard</h2>
        {% if user.is_staff %}
            <a href="{% url 'create_room' %}" class="btn btn-warning fw-bold">Post New Room</a>
        {% endif %}
    </div>

    <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#chats" type="button">My Chats</button></li>
        {% if user.is_staff %}
        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#rooms" type="button">My Listings</button></li>
        {% endif %}
    </ul>

    <div class="tab-content">
        <div class="tab-pane fade show active" id="chats">
            <div class="list-group">
                {% for chat in chats %}
                <a href="{% url 'chat_detail' chat.pk %}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-1 text-primary">{{ chat.room.title }}</h5>
                        <small class="text-muted">
                            {% if chat.sender == user %}
                                Chatting with Owner
                            {% else %}
                                Chatting with {{ chat.sender.username }}
                            {% endif %}
                        </small>
                    </div>
                    <span class="badge bg-secondary rounded-pill">View</span>
                </a>
                {% empty %}
                <div class="text-center py-5 text-muted">You haven't started any conversations yet.</div>
                {% endfor %}
            </div>
        </div>

        {% if user.is_staff %}
        <div class="tab-pane fade" id="rooms">
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead><tr><th>Title</th><th>Price</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for room in rooms %}
                        <tr>
                            <td>{{ room.title }}</td>
                            <td>${{ room.price_per_week }}</td>
                            <td>
                                <a href="{% url 'edit_room' room.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
                                <a href="{% url 'delete_room' room.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}"""

# 7. UPDATE ROOM_DETAIL.HTML (Add "Chat with Owner" button)
room_detail_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="row">
        <div class="col-md-8">
            {% if room.image %}<img src="{{ room.image.url }}" class="img-fluid rounded shadow-sm mb-4 w-100" style="max-height: 500px; object-fit: cover;">{% endif %}
            <h2 class="mb-2 fw-bold">{{ room.title }}</h2>
            <h3 class="text-primary fw-bold">${{ room.price_per_week }} <small class="text-muted fs-6">/week</small></h3>
            <p class="text-muted"><i class="bi bi-geo-alt-fill text-danger"></i> {{ room.address }}, {{ room.suburb }}</p>
            
            <div class="card bg-light border-0 p-3 mb-4"><h5 class="fw-bold">Inspection</h5><p class="mb-0 text-success fw-bold">{{ room.inspection_time|default:"Contact owner" }}</p></div>
            <p>{{ room.description|linebreaks }}</p>
            
            <div class="card border-primary mb-4">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div><h5 class="text-primary fw-bold">Ready to move in?</h5><p class="mb-0 small">Secure this room by paying the bond.</p></div>
                    <form action="{% url 'create_checkout_session' room.pk %}" method="POST">{% csrf_token %}<button class="btn btn-primary btn-lg">Pay Bond</button></form>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card shadow border-0 sticky-top" style="top: 20px;">
                <div class="card-header bg-dark text-white py-3"><h5 class="mb-0">Contact Owner</h5></div>
                <div class="card-body">
                    {% if user.is_authenticated %}
                        <p class="text-muted small">Start a live chat with the owner.</p>
                        <a href="{% url 'start_chat' room.pk %}" class="btn btn-success w-100 fw-bold py-2"><i class="bi bi-chat-dots-fill"></i> Chat Now</a>
                    {% else %}
                        <div class="text-center py-4">
                            <i class="bi bi-person-lock fs-1 text-muted"></i>
                            <h5 class="mt-3">Login to Chat</h5>
                            <a href="/accounts/login/" class="btn btn-primary w-100">Login</a>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

# Write Files
files = {
    'core/models.py': models_code,
    'core/forms.py': forms_code,
    'core/views.py': views_code,
    'core/urls.py': urls_code,
    'templates/core/chat.html': chat_html,
    'templates/core/dashboard.html': dashboard_html,
    'templates/core/room_detail.html': room_detail_html,
}

for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content.strip())
    print(f"Updated: {path}")

print("✅ Chat & Referral System Added!")
