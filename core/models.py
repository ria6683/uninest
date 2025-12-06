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