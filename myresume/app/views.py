
# =========================================================================
# File: app/views.py
# =========================================================================
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from .models import Resume
from .forms import ResumeForm
from xhtml2pdf import pisa
from django.conf import settings
from django.utils import timezone


def signup_view(request):
    """
    Handles user registration.
    If the form is valid, a new user is created and redirected to the login page.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

@login_required
def resume_list_view(request):
    """
    Displays a list of all resumes belonging to the logged-in user.
    """
    resumes = Resume.objects.filter(user=request.user)
    return render(request, 'resume/resume_list.html', {'resumes': resumes})

@login_required
def resume_create_view(request):
    """
    Handles the creation of a new resume.
    Initializes a form and saves the data with the current user.
    """
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            return redirect('app:resume_list')
    else:
        form = ResumeForm()
    return render(request, 'resume/resume_form.html', {'form': form, 'page_title': 'Create New Resume'})

@login_required
def resume_edit_view(request, pk):
    """
    Handles the editing of an existing resume.
    Only allows the user to edit their own resumes.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            form.save()
            return redirect('app:resume_list')
    else:
        form = ResumeForm(instance=resume)
    return render(request, 'resume/resume_form.html', {'form': form, 'page_title': 'Edit Resume'})

@login_required
def resume_detail_view(request, pk, template_name='template1'):
    """
    Displays a single resume using a selected template.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    return render(request, f'resume/templates/{template_name}.html', {'resume': resume})

@login_required
def resume_template_select_view(request, pk):
    """
    Allows the user to select a template for a specific resume.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    templates = ['template1', 'template2']
    return render(request, 'resume/template_select.html', {'resume': resume, 'templates': templates})

@login_required
def export_pdf_view(request, pk, template_name='template1'):
    """
    Generates a PDF file from the resume data and a chosen template.
    Uses xhtml2pdf to convert HTML content to a PDF document.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    # Render HTML content for the PDF using a specific template
    html_string = render_to_string(f'resume/pdf_templates/{template_name}_pdf.html', {'resume': resume})
    
    # Create a file-like object to write the PDF data into
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{resume.full_name}_resume.pdf"'
    
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=response,
        link_callback=lambda uri, rel: os.path.join(settings.BASE_DIR, uri.replace(settings.MEDIA_URL, 'media/'))
    )
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@login_required
def social_icons_list(request):
    social_icons = ['facebook', 'instagram', 'linkedin', 'github', 'youtube']
    return render(request, 'base.html', {
        'social_icons': social_icons,
        'now': timezone.now(),  # if you're using {{ now.year }} in the footer
    })
   