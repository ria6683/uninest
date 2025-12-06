import os

# 1. UPDATE MODELS (Adding Inspection Time)
models_code = """
from django.db import models
from django.contrib.auth.models import User

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
    
    # NEW FIELD: INSPECTION TIME
    inspection_time = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Saturday 10:00 AM - 11:00 AM")
    
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='room_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.suburb}"

class Inquiry(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='inquiries')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry for {self.room.title} from {self.name}"
"""

# 2. UPDATE FORMS (To allow typing the inspection time)
forms_code = """
from django import forms
from .models import Room, Inquiry
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hi, is this still available?'}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email']
"""

# 3. UPDATE VIEWS (To show messages in dashboard & handle payments)
views_code = """
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Room, Inquiry
from .forms import RoomForm, InquiryForm, RegisterForm

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
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.room = room
            inquiry.save()
            return redirect('room_detail', pk=pk)
    else:
        form = InquiryForm()
    return render(request, 'core/room_detail.html', {'room': room, 'form': form})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Get my rooms
    user_rooms = Room.objects.filter(owner=request.user).order_by('-created_at')
    # Get messages sent to my rooms
    user_inquiries = Inquiry.objects.filter(room__owner=request.user).order_by('-created_at')
    
    return render(request, 'core/dashboard.html', {'rooms': user_rooms, 'inquiries': user_inquiries})

@login_required
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
def delete_room(request, pk):
    room = get_object_or_404(Room, pk=pk, owner=request.user)
    if request.method == 'POST':
        room.delete()
        return redirect('dashboard')
    return render(request, 'core/room_confirm_delete.html', {'room': room})

@login_required
def payment_page(request, pk):
    room = get_object_or_404(Room, pk=pk)
    return render(request, 'core/payment.html', {'room': room})
"""

# 4. UPDATE URLS (Add payment link)
urls_code = """
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/pay/', views.payment_page, name='payment_page'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/create/', views.create_room, name='create_room'),
    path('dashboard/edit/<int:pk>/', views.edit_room, name='edit_room'),
    path('dashboard/delete/<int:pk>/', views.delete_room, name='delete_room'),
]
"""

# 5. NEW DASHBOARD HTML (With Messages Tab)
dashboard_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="bi bi-speedometer2"></i> My Dashboard</h2>
        <a href="{% url 'create_room' %}" class="btn btn-warning fw-bold">Post New Room</a>
    </div>

    <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
        <li class="nav-item">
            <button class="nav-link active" id="rooms-tab" data-bs-toggle="tab" data-bs-target="#rooms" type="button">My Listings</button>
        </li>
        <li class="nav-item">
            <button class="nav-link" id="messages-tab" data-bs-toggle="tab" data-bs-target="#messages" type="button">Inbox <span class="badge bg-danger">{{ inquiries.count }}</span></button>
        </li>
    </ul>

    <div class="tab-content" id="myTabContent">
        <div class="tab-pane fade show active" id="rooms">
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light"><tr><th>Image</th><th>Title</th><th>Price</th><th>Inspection</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for room in rooms %}
                        <tr>
                            <td width="100">
                                {% if room.image %}<img src="{{ room.image.url }}" width="80" class="rounded">{% else %}No Img{% endif %}
                            </td>
                            <td>{{ room.title }}<br><small class="text-muted">{{ room.suburb }}</small></td>
                            <td>${{ room.price_per_week }}</td>
                            <td>
                                {% if room.inspection_time %}
                                    <span class="badge bg-success">{{ room.inspection_time }}</span>
                                {% else %}
                                    <span class="badge bg-secondary">Not Set</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{% url 'edit_room' room.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
                                <a href="{% url 'delete_room' room.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
                            </td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="5" class="text-center py-4">You haven't posted any rooms yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="tab-pane fade" id="messages">
            <div class="list-group">
                {% for msg in inquiries %}
                <div class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1 text-primary">{{ msg.name }}</h5>
                        <small class="text-muted">{{ msg.created_at|date:"M d, Y" }}</small>
                    </div>
                    <p class="mb-1"><strong>Re: {{ msg.room.title }}</strong></p>
                    <p class="mb-1 fst-italic">"{{ msg.message }}"</p>
                    <small>Email: <a href="mailto:{{ msg.email }}">{{ msg.email }}</a></small>
                </div>
                {% empty %}
                <div class="text-center py-5 text-muted">No messages yet.</div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

# 6. UPDATE ROOM DETAIL HTML (Show Inspection + Payment Button)
room_detail_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="row">
        <div class="col-md-8">
            {% if room.image %}
                <img src="{{ room.image.url }}" class="img-fluid rounded shadow-sm mb-4 w-100" style="max-height: 500px; object-fit: cover;">
            {% endif %}
            
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h2 class="mb-2 fw-bold">{{ room.title }}</h2>
                    <p class="text-muted fs-5"><i class="bi bi-geo-alt-fill text-danger"></i> {{ room.address }}, {{ room.suburb }}</p>
                </div>
                <div class="text-end">
                    <h3 class="text-primary fw-bold">${{ room.price_per_week }}</h3>
                    <small class="text-muted">per week</small>
                </div>
            </div>

            <div class="card bg-light border-0 p-3 mb-4 mt-3">
                <h5 class="fw-bold"><i class="bi bi-calendar-check"></i> Inspection Time</h5>
                {% if room.inspection_time %}
                    <p class="mb-0 text-success fw-bold fs-5">{{ room.inspection_time }}</p>
                {% else %}
                    <p class="mb-0 text-muted">Contact owner to arrange inspection.</p>
                {% endif %}
            </div>

            <h5>Description</h5>
            <p class="text-muted" style="line-height: 1.8;">{{ room.description|linebreaks }}</p>
            
            <hr>
            
            <div class="card border-primary mb-4">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="text-primary fw-bold">Ready to move in?</h5>
                        <p class="mb-0 small">Secure this room by paying the bond online.</p>
                    </div>
                    <a href="{% url 'payment_page' room.pk %}" class="btn btn-primary btn-lg"><i class="bi bi-credit-card"></i> Pay Bond</a>
                </div>
            </div>

            <div class="ratio ratio-21x9 bg-secondary bg-opacity-10 border rounded">
                 <iframe src="https://maps.google.com/maps?q={{ room.address|urlencode }},{{ room.suburb|urlencode }}&output=embed"></iframe>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card shadow border-0 sticky-top" style="top: 20px;">
                <div class="card-header bg-dark text-white py-3">
                    <h5 class="mb-0">Contact Owner</h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        {{ form.as_p }}
                        <button type="submit" class="btn btn-success w-100 fw-bold py-2">Send Message</button>
                    </form>
                    <p class="text-muted small text-center mt-3 mb-0">The owner will receive this in their dashboard.</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

# 7. NEW PAYMENT PAGE HTML
payment_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-lg border-0">
                <div class="card-header bg-primary text-white text-center py-3">
                    <h4><i class="bi bi-shield-lock"></i> Secure Payment</h4>
                </div>
                <div class="card-body p-4">
                    <p class="text-muted text-center">You are paying the bond for:</p>
                    <h5 class="text-center mb-4">{{ room.title }}</h5>
                    
                    <div class="alert alert-info">
                        <strong>Amount Due:</strong> ${{ room.price_per_week }} (1 Week Bond)
                    </div>

                    <form onsubmit="alert('Payment Successful! (This is a demo)'); return false;">
                        <div class="mb-3">
                            <label class="form-label">Cardholder Name</label>
                            <input type="text" class="form-control" placeholder="John Doe" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Card Number</label>
                            <input type="text" class="form-control" placeholder="0000 0000 0000 0000" required>
                        </div>
                        <div class="row">
                            <div class="col-6 mb-3">
                                <label class="form-label">Expiry</label>
                                <input type="text" class="form-control" placeholder="MM/YY" required>
                            </div>
                            <div class="col-6 mb-3">
                                <label class="form-label">CVC</label>
                                <input type="text" class="form-control" placeholder="123" required>
                            </div>
                        </div>
                        <button class="btn btn-success w-100 btn-lg mt-3">Pay Now</button>
                        <a href="{% url 'room_detail' room.pk %}" class="btn btn-link w-100 mt-2 text-muted">Cancel</a>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

# WRITE FILES
files = {
    'core/models.py': models_code,
    'core/forms.py': forms_code,
    'core/views.py': views_code,
    'core/urls.py': urls_code,
    'templates/core/dashboard.html': dashboard_html,
    'templates/core/room_detail.html': room_detail_html,
    'templates/core/payment.html': payment_html,
}

for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content.strip())
    print(f"Updated: {path}")

print("✅ Code updated! NOW YOU MUST RUN MIGRATIONS.")

