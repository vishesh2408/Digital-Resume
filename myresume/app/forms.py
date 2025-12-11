# =========================================================================
# File: app/forms.py
# =========================================================================
from django import forms
from django.forms import inlineformset_factory, DateInput, Textarea
from .models import Resume, Project, Certification, EducationEntry, Extracurricular, Experience, Skill

# Accept several common month formats: HTML month inputs produce 'YYYY-MM',
# but users may paste or type 'July 2024' or 'Jul 2024'. We include day-format
# as a fallback.
MONTH_INPUT_FORMATS = ['%Y-%m', '%B %Y', '%b %Y', '%Y-%m-%d']

class BaseTWModelForm(forms.ModelForm):
    """
    Applies Tailwind classes to all widgets by default.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            base = 'w-full border rounded-md p-2'
            field.widget.attrs['class'] = (css + ' ' + base).strip()


class ResumeForm(BaseTWModelForm):
    """
    Django form for creating and updating Resume instances.
    It's a ModelForm, so it's automatically linked to the Resume model.
    """
    class Meta:
        model = Resume
        # We'll use all fields except 'user' which will be set automatically
        exclude = ['user', 'created_at', 'updated_at']

class ProjectForm(BaseTWModelForm):
    # Project end date comes from an HTML month picker or user text like 'July 2024'
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    class Meta:
        model = Project
        # Only end date
        fields = ['name', 'description', 'technologies_csv', 'url', 'end_date']
        # widget is already set by the explicit field above
        labels = {
            'end_date': 'End date',
        }

class CertificationForm(BaseTWModelForm):
    issue_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    expiry_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    class Meta:
        model = Certification
        fields = ['name', 'issuer', 'duration', 'issue_date', 'expiry_date', 'credential_id']

class EducationEntryForm(BaseTWModelForm):
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    class Meta:
        model = EducationEntry
        # Only completion date
        fields = ['institution', 'degree', 'field', 'location', 'end_date', 'gpa']
        labels = {
            'end_date': 'Completion date',
        }

class ExtracurricularForm(BaseTWModelForm):
    # Allow title/description/dates to be optional in the form (user requested)
    title = forms.CharField(required=False)
    description = forms.CharField(required=False, widget=Textarea(attrs={'rows': 3}))
    start_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    class Meta:
        model = Extracurricular
        fields = ['title', 'description', 'start_date', 'end_date']

class ExperienceForm(BaseTWModelForm):
    # Make textual fields optional per user request
    company = forms.CharField(required=False)
    position = forms.CharField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'month'}), input_formats=MONTH_INPUT_FORMATS)
    description = forms.CharField(required=False, widget=Textarea(attrs={'rows': 3}))
    achievements = forms.CharField(required=False, widget=Textarea(attrs={'rows': 3}))
    class Meta:
        model = Experience
        fields = ['company', 'position', 'location', 'start_date', 'end_date', 'current', 'description', 'achievements']

class SkillForm(BaseTWModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category', 'level']
        widgets = {
            'level': forms.NumberInput(attrs={'type': 'range', 'min': 1, 'max': 5, 'class': 'w-full'}),
        }

ProjectFormSet = inlineformset_factory(
    Resume, Project, form=ProjectForm, extra=1, can_delete=True
)

CertificationFormSet = inlineformset_factory(
    Resume, Certification, form=CertificationForm, extra=1, can_delete=True
)

EducationFormSet = inlineformset_factory(
    Resume, EducationEntry, form=EducationEntryForm, extra=1, can_delete=True
)

ExtracurricularFormSet = inlineformset_factory(
    Resume, Extracurricular, form=ExtracurricularForm, extra=1, can_delete=True
)

ExperienceFormSet = inlineformset_factory(
    Resume, Experience, form=ExperienceForm, extra=1, can_delete=True
)

SkillFormSet = inlineformset_factory(
    Resume, Skill, form=SkillForm, extra=1, can_delete=True
)