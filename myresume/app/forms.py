
# =========================================================================
# File: app/forms.py
# =========================================================================
from django import forms
from .models import Resume

class ResumeForm(forms.ModelForm):
    """
    Django form for creating and updating Resume instances.
    It's a ModelForm, so it's automatically linked to the Resume model.
    """
    class Meta:
        model = Resume
        # We'll use all fields except 'user' which will be set automatically
        exclude = ['user', 'created_at', 'updated_at']