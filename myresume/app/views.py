
# =========================================================================
# File: app/views.py
# =========================================================================
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db import transaction
from .models import Resume
from .forms import (
    ResumeForm,
    ProjectFormSet,
    CertificationFormSet,
    EducationFormSet,
    ExtracurricularFormSet,
    ExperienceFormSet,
    SkillFormSet,
)
from xhtml2pdf import pisa
from django.conf import settings
from django.utils import timezone
from .utils.ats import (
    analyze_text,
    analyze_resume_instance,
    analyze_text_with_jd,
    extract_text_from_pdf,
    extract_text_from_docx,
    build_resume_text,
    classify_improvements,
)

import tempfile
import logging
import time
from django.db import utils as db_utils
from weasyprint import HTML, CSS
from django.contrib.staticfiles import finders
import os
from playwright.sync_api import sync_playwright
import codecs
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


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
    return render(request, 'auth/signup.html', {'form': form, 'hide_header_footer': True})


def home_view(request):
    """Render the landing / hero page.

    This view is intentionally public and renders a full-screen hero that
    replaces the default navbar/footer (we pass hide_header_footer=True so
    the base template does not render its own header/footer). The hero's
    CTAs link to existing app routes (`app:ats_analysis` and `app:resume_list`).
    """
    social_icons = ['facebook', 'instagram', 'linkedin', 'github', 'youtube']
    return render(request, 'home.html', {
        'social_icons': social_icons,
        'now': timezone.now(),
        'hide_header_footer': True,
    })

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
        # We need a temporary instance for formsets; will set user and save atomically
        if form.is_valid():
            with transaction.atomic():
                resume = form.save(commit=False)
                resume.user = request.user
                # Explicitly capture Quill HTML fields from hidden inputs
                resume.summary = request.POST.get('summary', '')
                resume.save()
                project_formset = ProjectFormSet(request.POST, instance=resume, prefix='projects')
                cert_formset = CertificationFormSet(request.POST, instance=resume, prefix='certs')
                edu_formset = EducationFormSet(request.POST, instance=resume, prefix='edu')
                extra_formset = ExtracurricularFormSet(request.POST, instance=resume, prefix='extra')
                exp_formset = ExperienceFormSet(request.POST, instance=resume, prefix='exp')
                skill_formset = SkillFormSet(request.POST, instance=resume, prefix='skills')
                if all([project_formset.is_valid(), cert_formset.is_valid(), edu_formset.is_valid(), extra_formset.is_valid(), exp_formset.is_valid(), skill_formset.is_valid()]):
                    project_formset.save()
                    cert_formset.save()
                    edu_formset.save()
                    extra_formset.save()
                    exp_formset.save()
                    skill_formset.save()
                    return redirect('app:resume_list')
                else:
                    # If any formset invalid, rollback DB changes and render errors
                    transaction.set_rollback(True)
                    # Log errors to server console to help debugging
                    logger.error('Formset validation failed during resume creation')
                    logger.error('POST keys: %s', list(request.POST.keys()))
                    for name, fs in [('projects', project_formset), ('certs', cert_formset), ('edu', edu_formset), ('extra', extra_formset), ('exp', exp_formset), ('skills', skill_formset)]:
                        if not fs.is_valid():
                            logger.error('Formset %s errors: %s', name, fs.errors)
        # If form invalid or we rolled back due to formset errors, fall through to re-render with errors
        # Instantiate empty/unbound formsets only if they weren't already created above
        if 'project_formset' not in locals():
            project_formset = ProjectFormSet(prefix='projects')
        if 'cert_formset' not in locals():
            cert_formset = CertificationFormSet(prefix='certs')
        if 'edu_formset' not in locals():
            edu_formset = EducationFormSet(prefix='edu')
        if 'extra_formset' not in locals():
            extra_formset = ExtracurricularFormSet(prefix='extra')
        if 'exp_formset' not in locals():
            exp_formset = ExperienceFormSet(prefix='exp')
        if 'skill_formset' not in locals():
            skill_formset = SkillFormSet(prefix='skills')
    else:
        form = ResumeForm()
        project_formset = ProjectFormSet(prefix='projects')
        cert_formset = CertificationFormSet(prefix='certs')
        edu_formset = EducationFormSet(prefix='edu')
        extra_formset = ExtracurricularFormSet(prefix='extra')
        exp_formset = ExperienceFormSet(prefix='exp')
        skill_formset = SkillFormSet(prefix='skills')
    return render(request, 'resume/resume_form.html', {
        'form': form,
        'project_formset': project_formset,
        'cert_formset': cert_formset,
        'edu_formset': edu_formset,
        'extra_formset': extra_formset,
        'exp_formset': exp_formset,
        'skill_formset': skill_formset,
        'page_title': 'Create New Resume'
    })

@login_required
def resume_edit_view(request, pk):
    """
    Handles the editing of an existing resume.
    Only allows the user to edit their own resumes.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        project_formset = ProjectFormSet(request.POST, instance=resume, prefix='projects')
        cert_formset = CertificationFormSet(request.POST, instance=resume, prefix='certs')
        edu_formset = EducationFormSet(request.POST, instance=resume, prefix='edu')
        extra_formset = ExtracurricularFormSet(request.POST, instance=resume, prefix='extra')
        exp_formset = ExperienceFormSet(request.POST, instance=resume, prefix='exp')
        skill_formset = SkillFormSet(request.POST, instance=resume, prefix='skills')
        if form.is_valid() and all([
            project_formset.is_valid(), cert_formset.is_valid(), edu_formset.is_valid(), extra_formset.is_valid(), exp_formset.is_valid(), skill_formset.is_valid()
        ]):
                # Wrap save operations with a short retry/backoff to mitigate
                # transient SQLite "database is locked" errors in development.
                max_retries = 5
                backoff = 0.1
                last_exc = None
                for attempt in range(1, max_retries + 1):
                    try:
                        with transaction.atomic():
                            inst = form.save(commit=False)
                            # Ensure Quill HTML fields are updated from hidden inputs
                            inst.summary = request.POST.get('summary', inst.summary)
                            inst.save()
                            project_formset.save()
                            cert_formset.save()
                            edu_formset.save()
                            extra_formset.save()
                            exp_formset.save()
                            skill_formset.save()
                        last_exc = None
                        break
                    except db_utils.OperationalError as e:
                        last_exc = e
                        # Only retry on database locked; re-raise for other op errors
                        msg = str(e).lower()
                        if 'database is locked' in msg or 'database is busy' in msg:
                            logger.warning('Database locked on save attempt %s/%s for resume %s; retrying after %.2fs', attempt, max_retries, resume.pk, backoff)
                            time.sleep(backoff)
                            backoff *= 2
                            continue
                        else:
                            raise
                if last_exc:
                    # After retries, re-raise so the standard error handling shows the traceback
                    logger.error('Failed to save resume %s after %s attempts: %s', resume.pk, max_retries, last_exc)
                    raise last_exc
                return redirect('app:resume_list')
        else:
            # Log validation errors to help debugging
            logger.error('Resume edit validation failed for resume id %s by user %s', resume.pk, request.user)
            logger.error('POST keys: %s', list(request.POST.keys()))
            if not form.is_valid():
                logger.error('Resume form errors: %s', form.errors)
            for name, fs in [('projects', project_formset), ('certs', cert_formset), ('edu', edu_formset), ('extra', extra_formset), ('exp', exp_formset), ('skills', skill_formset)]:
                if not fs.is_valid():
                    logger.error('Formset %s errors: %s', name, fs.errors)
    else:
        form = ResumeForm(instance=resume)
        project_formset = ProjectFormSet(instance=resume, prefix='projects')
        cert_formset = CertificationFormSet(instance=resume, prefix='certs')
        edu_formset = EducationFormSet(instance=resume, prefix='edu')
        extra_formset = ExtracurricularFormSet(instance=resume, prefix='extra')
        exp_formset = ExperienceFormSet(instance=resume, prefix='exp')
        skill_formset = SkillFormSet(instance=resume, prefix='skills')
    return render(request, 'resume/resume_form.html', {
        'form': form,
        'project_formset': project_formset,
        'cert_formset': cert_formset,
        'edu_formset': edu_formset,
        'extra_formset': extra_formset,
        'exp_formset': exp_formset,
        'skill_formset': skill_formset,
        'page_title': 'Edit Resume'
    })

@login_required
def resume_detail_view(request, pk, template_name='template1'):
    """
    Displays a single resume using a selected template.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    return render(request, f'resume/templates/{template_name}.html', {'resume': resume, 'template_name': template_name})

@login_required
def resume_template_select_view(request, pk):
    """
    Allows the user to select a template for a specific resume.
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    templates = ['template1', 'template2', 'template3', 'template4', 'template5', 'template6']
    return render(request, 'resume/template_select.html', {'resume': resume, 'templates': templates})




@login_required
def export_pdf_view(request, pk, template_name):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    html_string = render_to_string(
        f'resume/templates/{template_name}.html',
        {
            'resume': resume,
            'request': request,
            'hide_header_footer': True,
            'template_name': template_name,
            # Attempt to fix double-escaped HTML coming from the stored summary
            # (e.g. literal "\u003Cp\u003E" sequences). Decode unicode-escape
            # sequences and pass a marked-safe summary to the template.
            'render_summary': (lambda s: (mark_safe(codecs.decode(s, 'unicode_escape')) if isinstance(s, str) and '\\u' in s else (mark_safe(s) if isinstance(s, str) else s)))(resume.summary if getattr(resume, 'summary', None) is not None else '')
        }
    )

    css_files = []
    tailwind_path = finders.find('css/tailwind.css')
    if tailwind_path:
        css_files.append(CSS(filename=tailwind_path))
    pdf_css_path = finders.find('css/pdf.css')
    if pdf_css_path:
        css_files.append(CSS(filename=pdf_css_path))
  
    template_css_candidate = f'css/{template_name}.css'
    template_css_path = finders.find(template_css_candidate)
    if template_css_path:
        css_files.append(CSS(filename=template_css_path))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
        ).write_pdf(tmp_pdf.name, stylesheets=css_files)
        tmp_pdf.seek(0)
        pdf_content = tmp_pdf.read()

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{resume.full_name}_resume.pdf"'
    return response


@login_required
def social_icons_list(request):
    social_icons = ['facebook', 'instagram', 'linkedin', 'github', 'youtube']
    return render(request, 'base.html', {
        'social_icons': social_icons,
        'now': timezone.now(),  # if you're using {{ now.year }} in the footer
    })
@login_required
def ats_analysis_view(request):
    analysis = None
    resumes = Resume.objects.filter(user=request.user)
    selected_pk = request.POST.get('resume_pk') if request.method == 'POST' else request.GET.get('resume_pk')
    if request.method == 'POST':
        # Optional JD file for comparison
        jd_text = (request.POST.get('job_description') or '').strip()
        if request.FILES.get('jd_upload'):
            jdf = request.FILES['jd_upload']
            name = (jdf.name or '').lower()
            data = jdf.read()
            if name.endswith('.pdf'):
                jd_text = extract_text_from_pdf(data)
            elif name.endswith('.docx'):
                jd_text = extract_text_from_docx(data)
            else:
                try:
                    jd_text = data.decode('utf-8', errors='ignore')
                except Exception:
                    jd_text = ''

        if selected_pk:
            try:
                resume = Resume.objects.get(pk=selected_pk, user=request.user)
                resume_text = build_resume_text(resume)
                if jd_text:
                    # Compute JD match over resume text, then classify improvements using context
                    analysis = analyze_text_with_jd(resume_text, jd_text)
                    context = {
                        'has_linkedin': bool(getattr(resume, 'linkedin', '') or ''),
                        'has_location': bool(getattr(resume, 'location', '') or ''),
                        'has_experience': hasattr(resume, 'experience_items') and resume.experience_items.exists(),
                        'employment_dates_present': all([(e.start_date or e.end_date) for e in getattr(resume, 'experience_items').all()]) if hasattr(resume, 'experience_items') and resume.experience_items.exists() else False,
                        'education_graduation_year_present': any([bool(ed.end_date) for ed in getattr(resume, 'education_items').all()]) if hasattr(resume, 'education_items') and resume.education_items.exists() else False,
                    }
                    analysis['improvements'] = classify_improvements(context=context, analysis=analysis)
                else:
                    # Use instance-aware analysis which already classifies improvements
                    analysis = analyze_resume_instance(resume)
            except Resume.DoesNotExist:
                analysis = {'error': 'Resume not found.'}
        elif request.FILES.get('upload'):
            up = request.FILES['upload']
            name = (up.name or '').lower()
            data = up.read()
            if name.endswith('.pdf'):
                content = extract_text_from_pdf(data)
            elif name.endswith('.docx'):
                content = extract_text_from_docx(data)
            else:
                try:
                    content = data.decode('utf-8', errors='ignore')
                except Exception:
                    content = ''
            if jd_text:
                analysis = analyze_text_with_jd(content, jd_text)
            else:
                analysis = analyze_text(content)
    return render(request, 'resume/ats_analysis.html', {
        'resumes': resumes,
        'analysis': analysis,
        'selected_pk': int(selected_pk) if selected_pk else None,
        'posted_jd_text': (request.POST.get('job_description') or '') if request.method == 'POST' else '',
    })
   