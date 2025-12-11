from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    """
    Model to store resume data.
    Each resume is linked to a specific user.
    The TextFields will store rich HTML content from the Quill editor.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Text fields for rich content, will be populated by Quill.js
    summary = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    training = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    education = models.TextField(blank=True)
    certificates = models.TextField(blank=True)

    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name}'s Resume"