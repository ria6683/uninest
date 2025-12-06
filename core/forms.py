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