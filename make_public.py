import os

# 1. UPDATE VIEWS.PY (Remove @login_required from Payment)
views_code = """
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
import stripe
from .models import Room, Inquiry
from .forms import RoomForm, InquiryForm, RegisterForm

stripe.api_key = settings.STRIPE_SECRET_KEY

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
            # Stay on page and show success logic if needed
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

# --- OWNER ONLY SECTIONS (LOGIN REQUIRED) ---

@login_required
def dashboard(request):
    user_rooms = Room.objects.filter(owner=request.user).order_by('-created_at')
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

# --- PUBLIC PAYMENT (NO LOGIN REQUIRED) ---

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

# 2. UPDATE ROOM_DETAIL.HTML (Show forms to everyone)
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
                    <form action="{% url 'create_checkout_session' room.pk %}" method="POST">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-primary btn-lg"><i class="bi bi-credit-card"></i> Pay Bond (Secure)</button>
                    </form>
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

# Write the files
with open('core/views.py', 'w') as f:
    f.write(views_code)

with open('templates/core/room_detail.html', 'w') as f:
    f.write(room_detail_html)

print("✅ Website is now Public (Guests can Pay & Contact)!")
