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