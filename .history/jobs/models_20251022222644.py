from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=200, blank=True, null=True)
    about = models.TextField(blank=True),
    location = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_employer = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    Company = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_followers_count(self):
        return self.followers.count()
    
    def get_following_count(self):
        return self.followig.count()
    
    def is_following(self, user):
        return self.followers.filter(follower= user).exists()
    
class Connection(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Company(models.Model):
    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('hospitality', 'Hospitality'),
        ('other', 'Other'),
    ]
    
    SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    location = models.CharField(max_length=200)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, default='technology')
    company_size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True)
    founded_year = models.IntegerField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def active_jobs_count(self):
        return self.jobs.count()
    
    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'company_id': self.id})

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]
    
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='jobs')  # Make nullable
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    date_posted = models.DateTimeField(default=timezone.now)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-populate company_name from Company if company is set
        if self.company and not self.company_name:
            self.company_name = self.company.name
        super().save(*args, **kwargs)

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', '📝 Pending'),
        ('reviewed', '👀 Reviewed'),
        ('interview', '💼 Interview'),
        ('rejected', '❌ Rejected'),
        ('accepted', '✅ Accepted'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    date_applied = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the application")
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
    
    def save(self, *args, **kwargs):
        # Auto-populate full_name and email from user if not provided
        if not self.full_name and self.applicant:
            self.full_name = f"{self.applicant.first_name} {self.applicant.last_name}".strip()
            if not self.full_name:
                self.full_name = self.applicant.username
        if not self.email and self.applicant:
            self.email = self.applicant.email
        super().save(*args, **kwargs)

class JobAlert(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('instant', 'Instant'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, help_text="Name for this alert")
    keywords = models.TextField(help_text="Comma-separated keywords (e.g. python, django, remote)")
    location = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=50, blank=True, null=True, choices=Job.JOB_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_sent = models.DateTimeField(blank=True, null=True)
    
    def get_matching_jobs(self):
        """Get jobs that match this alert's criteria"""
        jobs = Job.objects.all()
        
        # Filter by keywords
        if self.keywords:
            keywords = self.get_keywords_list()
            query = Q()
            for keyword in keywords:
                query |= Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(company_name__icontains=keyword)  # Changed to company_name
            jobs = jobs.filter(query)
        
        # Filter by location
        if self.location:
            jobs = jobs.filter(location__icontains=self.location)
        
        # Filter by job type
        if self.job_type:
            jobs = jobs.filter(job_type=self.job_type)
        
        # Exclude jobs user has already applied to
        jobs = jobs.exclude(application__applicant=self.user)
        
        # Exclude jobs user posted
        jobs = jobs.exclude(posted_by=self.user)
        
        # Only get recent jobs (last 7 days)
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        jobs = jobs.filter(date_posted__gte=one_week_ago)
        
        return jobs.order_by('-date_posted')
    


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"

class ParsedResume(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='parsed_data')
    raw_text = models.TextField()
    processed_text = models.TextField(blank=True)
    
    # Personal Information
    full_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    # Education
    education = models.JSONField(default=dict, blank=True)  # Store as list of dicts
    
    # Experience
    experience = models.JSONField(default=dict, blank=True)  # Store as list of dicts
    
    # Skills
    skills = models.JSONField(default=list, blank=True)  # Store as list
    
    # Summary/Objective
    summary = models.TextField(blank=True)
    
    # Analysis results
    years_experience = models.FloatField(default=0)
    education_level = models.CharField(max_length=100, blank=True)
    primary_skills = models.JSONField(default=list, blank=True)
    
    parsed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Parsed: {self.resume.original_filename}"