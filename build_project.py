import os

# 1. SETTINGS.PY
settings_code = """
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-mac-setup-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'melbourne_rentals.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'melbourne_rentals.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [] 

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Australia/Melbourne'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
"""

# 2. MAIN URLS.PY
main_urls_code = """
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""

# 3. MODELS.PY
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
        return f"Inquiry for {self.room.title}"
"""

# 4. FORMS.PY
forms_code = """
from django import forms
from .models import Room, Inquiry
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['title', 'suburb', 'address', 'price_per_week', 'room_type', 'availability_date', 'description', 'image']
        widgets = {
            'availability_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email']
"""

# 5. ADMIN.PY
admin_code = """
from django.contrib import admin
from .models import Room, Inquiry

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'suburb', 'price_per_week', 'owner')
    list_filter = ('suburb', 'room_type')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'room', 'created_at')
"""

# 6. VIEWS.PY
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
    sort_by = request.GET.get('sort', '-created_at')

    rooms = Room.objects.all()

    if query:
        rooms = rooms.filter(Q(suburb__icontains=query) | Q(title__icontains=query))
    if min_price:
        rooms = rooms.filter(price_per_week__gte=min_price)
    if max_price:
        rooms = rooms.filter(price_per_week__lte=max_price)
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    
    if sort_by == 'price_asc':
        rooms = rooms.order_by('price_per_week')
    elif sort_by == 'price_desc':
        rooms = rooms.order_by('-price_per_week')
    else:
        rooms = rooms.order_by('-created_at')

    paginator = Paginator(rooms, 9)
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
    user_rooms = Room.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'core/dashboard.html', {'rooms': user_rooms})

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
"""

# 7. APP URLS.PY
app_urls_code = """
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/create/', views.create_room, name='create_room'),
    path('dashboard/edit/<int:pk>/', views.edit_room, name='edit_room'),
    path('dashboard/delete/<int:pk>/', views.delete_room, name='delete_room'),
]
"""

# HTML TEMPLATES

base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melbourne Rentals</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
</head>
<body class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏙️ Melbourne Rentals</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/rooms/">Browse</a>
                {% if user.is_authenticated %}
                    <a class="nav-link" href="/dashboard/">Dashboard</a>
                    <form action="/accounts/logout/" method="post" class="d-inline">
                        {% csrf_token %}
                        <button class="btn nav-link" type="submit">Logout</button>
                    </form>
                {% else %}
                    <a class="nav-link" href="/accounts/login/">Login</a>
                    <a class="btn btn-primary ms-2" href="/register/">Post Room</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <main class="flex-grow-1">
        {% block content %}{% endblock %}
    </main>
    <footer class="bg-light text-center py-3 mt-4"><p>© 2025 Melbourne Rentals</p></footer>
</body>
</html>"""

home_html = """{% extends 'base.html' %}
{% block content %}
<section class="bg-primary text-white text-center py-5" style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)), url('https://source.unsplash.com/1600x900/?melbourne,city') center/cover;">
    <div class="container">
        <h1 class="display-4 fw-bold">Find Your Home in Melbourne</h1>
        <div class="card p-3 mt-4 text-dark mx-auto" style="max-width: 800px;">
            <form action="{% url 'room_list' %}" method="get" class="row g-2">
                <div class="col-md-5"><input type="text" name="q" class="form-control" placeholder="Suburb (e.g. Carlton)"></div>
                <div class="col-md-4"><input type="number" name="max_price" class="form-control" placeholder="Max Price"></div>
                <div class="col-md-3"><button type="submit" class="btn btn-success w-100">Search</button></div>
            </form>
        </div>
    </div>
</section>
<div class="container py-5">
    <h3>Latest Listings</h3>
    <div class="row">
        {% for room in latest_rooms %}
        <div class="col-md-4 mb-3">
            <div class="card h-100">
                {% if room.image %}<img src="{{ room.image.url }}" class="card-img-top" style="height:200px;object-fit:cover;">{% endif %}
                <div class="card-body">
                    <h5>{{ room.title }}</h5>
                    <p class="text-muted">{{ room.suburb }}</p>
                    <h6 class="text-primary">${{ room.price_per_week }}/week</h6>
                    <a href="{% url 'room_detail' room.pk %}" class="btn btn-outline-primary w-100">View</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

room_list_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-4">
    <h2>Available Rooms</h2>
    <div class="row">
        {% for room in page_obj %}
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
                {% if room.image %}<img src="{{ room.image.url }}" class="card-img-top" style="height:180px;object-fit:cover;">{% endif %}
                <div class="card-body">
                    <h5>{{ room.title }}</h5>
                    <p>{{ room.suburb }} - ${{ room.price_per_week }}</p>
                    <a href="{% url 'room_detail' room.pk %}" class="btn btn-primary w-100">Details</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

room_detail_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="row">
        <div class="col-md-8">
            {% if room.image %}<img src="{{ room.image.url }}" class="img-fluid mb-4 w-100">{% endif %}
            <h2>{{ room.title }}</h2>
            <h4>${{ room.price_per_week }} / week</h4>
            <p>{{ room.description }}</p>
            <p><strong>Location:</strong> {{ room.address }}, {{ room.suburb }}</p>
            <p><strong>Available:</strong> {{ room.availability_date }}</p>
        </div>
        <div class="col-md-4">
            <div class="card p-3">
                <h5>Contact Owner</h5>
                <form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-success w-100">Send</button></form>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

dashboard_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>My Listings</h2>
        <a href="{% url 'create_room' %}" class="btn btn-success">Add New Room</a>
    </div>
    <div class="table-responsive">
        <table class="table table-hover">
            <thead><tr><th>Title</th><th>Suburb</th><th>Price</th><th>Actions</th></tr></thead>
            <tbody>
                {% for room in rooms %}
                <tr>
                    <td>{{ room.title }}</td>
                    <td>{{ room.suburb }}</td>
                    <td>${{ room.price_per_week }}</td>
                    <td>
                        <a href="{% url 'edit_room' room.pk %}" class="btn btn-sm btn-primary">Edit</a>
                        <a href="{% url 'delete_room' room.pk %}" class="btn btn-sm btn-danger">Delete</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}"""

room_form_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <h2>{{ title }}</h2>
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-success">Save Room</button>
        <a href="{% url 'dashboard' %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}"""

delete_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5 text-center">
    <h2>Are you sure?</h2>
    <p>Do you really want to delete "{{ room.title }}"?</p>
    <form method="post">{% csrf_token %}<button class="btn btn-danger">Yes, Delete</button> <a href="{% url 'dashboard' %}" class="btn btn-secondary">Cancel</a></form>
</div>
{% endblock %}"""

login_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5" style="max-width:400px;">
    <h2>Login</h2>
    <form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary w-100">Login</button></form>
</div>
{% endblock %}"""

register_html = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5" style="max-width:400px;">
    <h2>Register</h2>
    <form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-success w-100">Sign Up</button></form>
</div>
{% endblock %}"""

# WRITING FILES
files = {
    'melbourne_rentals/settings.py': settings_code,
    'melbourne_rentals/urls.py': main_urls_code,
    'core/models.py': models_code,
    'core/forms.py': forms_code,
    'core/admin.py': admin_code,
    'core/views.py': views_code,
    'core/urls.py': app_urls_code,
    'templates/base.html': base_html,
    'templates/core/home.html': home_html,
    'templates/core/room_list.html': room_list_html,
    'templates/core/room_detail.html': room_detail_html,
    'templates/core/dashboard.html': dashboard_html,
    'templates/core/room_form.html': room_form_html,
    'templates/core/room_confirm_delete.html': delete_html,
    'templates/registration/login.html': login_html,
    'templates/registration/register.html': register_html,
}

for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content.strip())
    print(f"Created: {path}")

print("✅ Project files generated successfully!")

