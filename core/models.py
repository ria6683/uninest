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