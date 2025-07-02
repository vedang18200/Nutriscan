
from django.contrib.auth.models import AbstractUser
from django.db import models
import json

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    ACTIVITY_LEVELS = [
        ('sedentary', 'Sedentary'),
        ('light', 'Lightly Active'),
        ('moderate', 'Moderately Active'),
        ('very', 'Very Active'),
        ('extra', 'Extra Active'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVELS, default='moderate')
    
    # Health information stored as JSON for flexibility
    health_conditions = models.JSONField(default=list, help_text="List of health conditions")
    allergies = models.JSONField(default=list, help_text="List of allergies")
    dietary_restrictions = models.JSONField(default=list, help_text="Dietary restrictions")
    health_goals = models.JSONField(default=list, help_text="Health goals")
    medications = models.JSONField(default=list, help_text="Current medications")
    
    # UAE specific
    emirates_resident = models.BooleanField(default=True)
    preferred_language = models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('ar', 'Arabic')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Profile"
