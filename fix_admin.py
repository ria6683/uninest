import os

# UPDATED ADMIN.PY (Compatible with Chat & Referrals)
admin_code = """
from django.contrib import admin
from .models import Room, Inquiry, Message, Profile

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'suburb', 'price_per_week', 'owner')
    list_filter = ('suburb', 'room_type')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    # Updated to show Chat details instead of old Name/Email
    list_display = ('id', 'room', 'sender', 'recipient', 'created_at')
    list_filter = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'inquiry', 'created_at', 'text_preview')
    
    def text_preview(self, obj):
        return obj.text[:50]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'referred_by')
"""

with open('core/admin.py', 'w') as f:
    f.write(admin_code)

print("✅ Admin Panel fixed!")
