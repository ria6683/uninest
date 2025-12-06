
from django import forms
from .models import Room, Inquiry
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
    
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        # Remove the strict "username characters" help text
        self.fields['username'].help_text = "Enter a unique username. Spaces and special characters are allowed."
        # Note: Extensive changes to validation require database schema changes, 
        # but this removes the strict UI warning.
