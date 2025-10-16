from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        # Auto-populate company_name from Company if company is set
        if self.company and not self.company_name:
            self.company_name = self.company.name
        super().save(*args, **kwargs)


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]
    
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    Company = models.ForeignKey(company, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200)
    description = models.TextField()
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    date_posted = models.DateTimeField(default=timezone.now)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title


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
    status = models.CharField(max_length=20, choices= STATUS_CHOICES, default='pending')
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

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def get_keywords_list(self):
        """Convert comma-separated keywords to list"""
        if self.keywords:
            return [keyword.strip().lower() for keyword in self.keywords.split(',')]
        return []

    def get_matching_jobs(self):
        """Get jobs that match this alert's criteria"""
        jobs = Job.objects.all()
        
        # Filter by keywords
        if self.keywords:
            keywords = self.get_keywords_list()
            query = Q()
            for keyword in keywords:
                query |= Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(company__icontains=keyword)
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

    def has_new_matches(self):
        """Check if there are new jobs matching this alert"""
        if not self.last_sent:
            return self.get_matching_jobs().exists()
        
        # Only count jobs posted after last alert was sent
        new_jobs = self.get_matching_jobs().filter(date_posted__gt=self.last_sent)
        return new_jobs.exists()

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
        return self.job_set.count()
    
    def get_absolute_url(self):
        return self.reverse('company_detail', kwargs={'company_id': self.id})

