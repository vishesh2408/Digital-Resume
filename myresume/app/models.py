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
    location = models.CharField(max_length=150, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    website = models.URLField(blank=True)
    
   
    summary = models.TextField(blank=True)

    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name}'s Resume"


class Project(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='project_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    technologies_csv = models.CharField(max_length=300, blank=True, help_text="Comma-separated technologies")
    url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class Certification(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='certification_items')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, blank=True)
    # Optional pretty string like "Dec’ 24"
    duration = models.CharField(max_length=20, blank=True, help_text="e.g., Dec’ 24")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class EducationEntry(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='education_items')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=150)
    field = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    gpa = models.CharField(max_length=20, blank=True, help_text="GPA/CGPA")

    def __str__(self):
        return f"{self.institution} - {self.degree}"


class Extracurricular(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='extracurricular_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Experience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experience_items')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    achievements = models.TextField(blank=True, help_text="Optional bullet points, one per line")

    def __str__(self):
        return f"{self.position} @ {self.company}"


class Skill(models.Model):
    CATEGORY_CHOICES = (
        ("Technical", "Technical"),
        ("Soft Skills", "Soft Skills"),
        ("Languages", "Languages"),
        ("Tools", "Tools"),
    )
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skill_items')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Technical")
    level = models.IntegerField(default=3)

    def __str__(self):
        return self.name