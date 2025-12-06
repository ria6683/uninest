from django.contrib import admin
from .models import Room, Inquiry

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'suburb', 'price_per_week', 'owner')
    list_filter = ('suburb', 'room_type')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'room', 'created_at')