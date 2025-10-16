from django import forms
from .models import Job, Application, UserProfile, JobAlert, Company

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company_name', 'description', 'location', 'salary', 'job_type']  # Remove 'company'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),  # Use company_name instead
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Why are you interested in this position?'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['headline', 'location', 'bio', 'profile_picture', 'website', 'resume']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Developer'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Kenya'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
        }

class JobAlertForm(forms.ModelForm):
    class Meta:
        model = JobAlert
        fields = ['name', 'keywords', 'location', 'job_type', 'frequency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python Developer Alerts'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter comma-separated keywords (e.g., python, django, remote, senior)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nairobi, Remote, Kenya'
            }),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'keywords': 'Enter relevant keywords separated by commas',
            'name': 'Give this alert a memorable name',
        }

    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords')
        if keywords:
            # Validate that we have at least one keyword
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            if not keyword_list:
                raise forms.ValidationError("Please enter at least one keyword")
        return keywords

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'logo', 'location', 'industry', 'company_size', 'founded_year', 'contact_email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your company...'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Nairobi, Kenya'}),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2020'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@company.com'}),
        }
        help_texts = {
            'name': 'The official name of your company',
            'description': 'Tell job seekers about your company culture, mission, and values',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Company.objects.filter(name__iexact=name).exists():
            if self.instance and self.instance.name == name:
                return name
            raise forms.ValidationError("A company with this name already exists.")
        return name