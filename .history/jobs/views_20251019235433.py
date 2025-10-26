from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, Application, UserProfile, JobAlert, Company
from .forms import JobForm, ApplicationForm, UserProfileForm, JobAlertForm,CompanyForm
from django.db.models import Q
from django.utils import timezone
from .emails import send_new_application_email, send_application_status_email
from .models import Resume, ParsedResume
from django.http import JsonResponse
import os
from django.conf import settings
import uuid
import json
import re


@login_required
def dashboard(request):
    # Get or create user profile
    UserProfile.objects.get_or_create(user=request.user)
    
    user_jobs = Job.objects.filter(posted_by=request.user).order_by('-date_posted')
    user_applications = Application.objects.filter(applicant=request.user).order_by('-date_applied')
    
    # Recent activity (last 5 applications and jobs)
    recent_applications = user_applications[:5]
    recent_jobs_posted = user_jobs[:5]
    
    # Application statistics
    application_stats = {
        'total': user_applications.count(),
        'pending': user_applications.filter(status='pending').count(),
        'reviewed': user_applications.filter(status='reviewed').count(),
        'interview': user_applications.filter(status='interview').count(),
        'accepted': user_applications.filter(status='accepted').count(),
        'rejected': user_applications.filter(status='rejected').count(),
    }
    
    # Job statistics - Calculate total applications for user's jobs
    total_applications_to_my_jobs = 0
    for job in user_jobs:
        total_applications_to_my_jobs += job.application_set.count()
    
    job_stats = {
        'total': user_jobs.count(),
        'active': user_jobs.count(),  # You can add an 'active' field to Job model later
        'total_applications': total_applications_to_my_jobs,
    }
    
    # Recommended jobs (simple implementation) - FIXED QUERY
    recommended_jobs = Job.objects.exclude(
        posted_by=request.user
    ).exclude(
        application__applicant=request.user  # Use application__applicant instead of applications__applicant
    ).order_by('-date_posted')[:3]
    
    context = {
        'user_jobs': user_jobs,
        'user_applications': user_applications,
        'recent_applications': recent_applications,
        'recent_jobs_posted': recent_jobs_posted,
        'application_stats': application_stats,
        'job_stats': job_stats,
        'recommended_jobs': recommended_jobs,
    }
    return render(request, 'jobs/dashboard.html', context)

@login_required
def profile(request):
    # Get or create user profile - this handles both new and existing users
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if created:
        messages.info(request, 'Profile created! Please update your information.')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'jobs/profile.html', {'form': form})

@login_required
def my_applications(request):
    applications = Application.objects.filter(applicant=request.user).order_by('-date_applied')
    
    # Calculate status counts
    status_counts = {
        'pending': applications.filter(status='pending').count(),
        'reviewed': applications.filter(status='reviewed').count(),
        'interview': applications.filter(status='interview').count(),
        'rejected': applications.filter(status='rejected').count(),
        'accepted': applications.filter(status='accepted').count(),
    }
    
    context = {
        'applications': applications,
        'status_counts': status_counts,
    }
    return render(request, 'jobs/my_applications.html', context)
@login_required
def manage_jobs(request):
    jobs = Job.objects.filter(posted_by=request.user).order_by('-date_posted')
    
    # Add application counts to each job
    jobs_with_counts = []
    for job in jobs:
        job.application_count = job.application_set.count()
        jobs_with_counts.append(job)
    
    return render(request, 'jobs/manage_jobs.html', {'jobs': jobs_with_counts})

@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    applications = Application.objects.filter(job=job).order_by('-date_applied')
    return render(request, 'jobs/job_applications.html', {'job': job, 'applications': applications})

# Your existing functions...
def home(request):
    latest_jobs = Job.objects.all().order_by('-date_posted')[:3]
    return render(request, 'jobs/home.html', {'latest_jobs': latest_jobs})



def job_list(request):
    jobs = Job.objects.all().order_by('-date_posted')
    
    # Get search parameters
    search_query = request.GET.get('q', '')
    job_type = request.GET.get('job_type', '')
    location = request.GET.get('location', '')
    
    # Apply filters
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(company_name__icontains=search_query) |  # Use company_name, not company
            Q(location__icontains=search_query)
        )
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    # Get unique locations for filter dropdown
    unique_locations = Job.objects.values_list('location', flat=True).distinct()
    
    context = {
        'jobs': jobs,
        'search_query': search_query,
        'selected_job_type': job_type,
        'selected_location': location,
        'job_types': Job.JOB_TYPE_CHOICES,
        'locations': unique_locations,
    }
    return render(request, 'jobs/job_list.html', context)

@login_required
def post_job(request):
    # Get user's companies for dropdown
    user_companies = Company.objects.filter(created_by=request.user)
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            
            # Handle company selection
            company_id = request.POST.get('company')
            if company_id:
                company = get_object_or_404(Company, id=company_id, created_by=request.user)
                job.company = company
                job.company_name = company.name
            else:
                # If no company selected, create a default company or use existing
                default_company, created = Company.objects.get_or_create(
                    name=job.company_name,
                    defaults={
                        'description': f'Company profile for {job.company_name}',
                        'location': job.location,
                        'created_by': request.user,
                    }
                )
                job.company = default_company
            
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('job_list')
    else:
        form = JobForm()
    
    return render(request, 'jobs/post_job.html', {
        'form': form,
        'user_companies': user_companies,

    })
def job_detail(request, job_id):
    """View details of a specific job"""
    job = get_object_or_404(Job, pk=job_id)
    
    # Check if user has already applied to this job
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(
            job=job, 
            applicant=request.user
        ).exists()
    
    context = {
        'job': job,
        'has_applied': has_applied,
    }
    return render(request, 'jobs/job_detail.html', context)
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user has already applied for this job
    existing_application = Application.objects.filter(applicant=request.user, job=job).first()
    if existing_application:
        messages.warning(request, 'You have already applied for this job!')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.job = job
            application.save()
            
            # Send email notification to employer
            try:
                send_new_application_email(application)
                messages.success(request, 'Application submitted successfully! Notification sent to employer.')
            except Exception as e:
                messages.success(request, 'Application submitted successfully! (Email notification failed)')
                # Log the error but don't show it to user
            
            return redirect('job_detail', job_id=job.id)
    else:
        form = ApplicationForm()
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

@login_required
def manage_job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    applications = Application.objects.filter(job=job).order_by('-date_applied')
    
    # Status counts for dashboard
    status_counts = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'reviewed': applications.filter(status='reviewed').count(),
        'interview': applications.filter(status='interview').count(),
        'rejected': applications.filter(status='rejected').count(),
        'accepted': applications.filter(status='accepted').count(),
    }
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    context = {
        'job': job,
        'applications': applications,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    }
    return render(request, 'jobs/manage_applications.html', context)

from .emails import send_application_status_email

@login_required
def update_application_status(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        # Check if the current user is the job poster
        if application.job.posted_by != request.user:
            messages.error(request, 'You do not have permission to update this application.')
            return redirect('dashboard')
        
        old_status = application.status
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            if notes:
                application.notes = notes
            application.save()
            
            # Send email notification to applicant
            try:
                send_application_status_email(application, old_status)
            except Exception as e:
                # Log error but don't show to user
                pass
            
            messages.success(request, f'Application status updated to {dict(Application.STATUS_CHOICES)[new_status]}')
        else:
            messages.error(request, 'Invalid status selected.')
        
        return redirect('job_applications', job_id=application.job.id)

@login_required
def view_application_detail(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    # Check if user has permission (either applicant or job poster)
    if request.user != application.applicant and request.user != application.job.posted_by:
        messages.error(request, 'You do not have permission to view this application.')
        return redirect('dashboard')
    
    context = {
        'application': application,
        'is_employer': request.user == application.job.posted_by,
    }
    return render(request, 'jobs/application_detail.html', context)

@login_required
def job_alerts(request):
    """View and manage job alerts"""
    alerts = JobAlert.objects.filter(user=request.user).order_by('-created_at')
    
    # Count new matches for each alert
    for alert in alerts:
        alert.new_matches_count = alert.get_matching_jobs().count()
    
    return render(request, 'jobs/job_alerts.html', {
        'alerts': alerts,
    })

@login_required
def create_job_alert(request):
    """Create a new job alert"""
    if request.method == 'POST':
        form = JobAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            messages.success(request, f'Job alert "{alert.name}" created successfully!')
            return redirect('job_alerts')
    else:
        form = JobAlertForm()
    
    return render(request, 'jobs/create_job_alert.html', {'form': form})

@login_required
def edit_job_alert(request, alert_id):
    """Edit an existing job alert"""
    alert = get_object_or_404(JobAlert, id=alert_id, user=request.user)
    
    if request.method == 'POST':
        form = JobAlertForm(request.POST, instance=alert)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job alert "{alert.name}" updated successfully!')
            return redirect('job_alerts')
    else:
        form = JobAlertForm(instance=alert)
    
    return render(request, 'jobs/edit_job_alert.html', {
        'form': form,
        'alert': alert,
    })

@login_required
def toggle_job_alert(request, alert_id):
    """Toggle job alert active/inactive"""
    alert = get_object_or_404(JobAlert, id=alert_id, user=request.user)
    alert.is_active = not alert.is_active
    alert.save()
    
    status = "activated" if alert.is_active else "deactivated"
    messages.success(request, f'Job alert "{alert.name}" {status}!')
    return redirect('job_alerts')

@login_required
def delete_job_alert(request, alert_id):
    """Delete a job alert"""
    alert = get_object_or_404(JobAlert, id=alert_id, user=request.user)
    alert_name = alert.name
    alert.delete()
    messages.success(request, f'Job alert "{alert_name}" deleted successfully!')
    return redirect('job_alerts')

@login_required
def view_alert_matches(request, alert_id):
    """View jobs that match a specific alert"""
    alert = get_object_or_404(JobAlert, id=alert_id, user=request.user)
    matching_jobs = alert.get_matching_jobs()
    
    # Mark as sent (for demo purposes - in real app, this would be in a cron job)
    alert.last_sent = timezone.now()
    alert.save()
    
    return render(request, 'jobs/alert_matches.html', {
        'alert': alert,
        'jobs': matching_jobs,
        'jobs_count': matching_jobs.count(),
    })

@login_required
def create_company(request):
    """Create a new company profile"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            messages.success(request, f'Company "{company.name}" created successfully!')
            return redirect('company_detail', company_id=company.id)
    else:
        form = CompanyForm()
    
    return render(request, 'jobs/create_company.html', {'form': form})

def company_detail(request, company_id):
    """View company profile and their jobs"""
    company = get_object_or_404(Company, id=company_id)
    # Use company_name to find jobs
    jobs = Job.objects.filter(company_name__iexact=company.name).order_by('-date_posted')
    
    # Check if user can edit this company
    can_edit = request.user == company.created_by or request.user.is_superuser
    
    context = {
        'company': company,
        'jobs': jobs,
        'can_edit': can_edit,
        'jobs_count': jobs.count(),
    }
    return render(request, 'jobs/company_detail.html', context)

@login_required
def edit_company(request, company_id):
    """Edit company profile"""
    company = get_object_or_404(Company, id=company_id)
    
    # Check permission
    if request.user != company.created_by and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this company.')
        return redirect('company_detail', company_id=company.id)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f'Company "{company.name}" updated successfully!')
            return redirect('company_detail', company_id=company.id)
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'jobs/edit_company.html', {
        'form': form,
        'company': company,
    })

def company_list(request):
    """List all companies"""
    companies = Company.objects.all().order_by('name')
    
    # Filter by industry if provided
    industry = request.GET.get('industry', '')
    if industry:
        companies = companies.filter(industry=industry)
    
    context = {
        'companies': companies,
        'industry_filter': industry,
        'industry_choices': Company.INDUSTRY_CHOICES,
    }
    return render(request, 'jobs/company_list.html', context)

@login_required
def my_companies(request):
    """View companies created by the user"""
    companies = Company.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Add job counts for each company (using company_name)
    for company in companies:
        company.jobs_count = Job.objects.filter(company_name__iexact=company.name).count()
    
    return render(request, 'jobs/my_companies.html', {'companies': companies})

@login_required
def upload_resume(request):
    if request.method == 'POST' and request.FILES.get('resume'):
        resume_file = request.FILES['resume']
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if resume_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT.'})
        
        # Save resume
        resume = Resume(
            user=request.user,
            file=resume_file,
            original_filename=resume_file.name,
            file_type=resume_file.name.split('.')[-1].lower()
        )
        resume.save()
        
        # Parse resume
        parser = ResumeParser()
        file_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
        parsed_data = parser.parse_resume(file_path, resume.file_type)
        
        if parsed_data:
            # Save parsed data
            parsed_resume = ParsedResume(
                resume=resume,
                raw_text=parsed_data['raw_text'],
                full_name=parsed_data['personal_info']['full_name'],
                email=parsed_data['personal_info']['email'],
                phone=parsed_data['personal_info']['phone'],
                location=parsed_data['personal_info']['location'],
                education=parsed_data['education'],
                experience=parsed_data['experience'],
                skills=parsed_data['skills'],
                summary=parsed_data['summary'],
                years_experience=parsed_data['years_experience']
            )
            parsed_resume.save()
            
            resume.processed = True
            resume.save()
            
            return JsonResponse({
                'success': True,
                'resume_id': resume.id,
                'summary': parsed_data['summary']
            })
    
    return render(request, 'upload_resume.html')

@login_required
def resume_analysis(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        parsed_data = ParsedResume.objects.get(resume=resume)
        
        context = {
            'resume': resume,
            'parsed_data': parsed_data
        }
        
        return render(request, 'resume_analysis.html', context)
    except (Resume.DoesNotExist, ParsedResume.DoesNotExist):
        return redirect('upload_resume')

@login_required
def resume_list(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'resume_list.html', {'resumes': resumes})

def match_resume_to_jobs(request, resume_id):
    """Match a parsed resume to relevant jobs"""
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        parsed_data = ParsedResume.objects.get(resume=resume)
        
        # Get all jobs
        jobs = Job.objects.all()  # Assuming you have a Job model
        matched_jobs = []
        
        for job in jobs:
            score = calculate_match_score(parsed_data, job)
            if score > 0.3:  # Only show jobs with >30% match
                matched_jobs.append({
                    'job': job,
                    'match_score': round(score * 100, 1)
                })
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return render(request, 'job_matches.html', {
            'resume': resume,
            'matched_jobs': matched_jobs
        })
    except (Resume.DoesNotExist, ParsedResume.DoesNotExist):
        return redirect('resume_list')

def calculate_match_score(parsed_resume, job):
    """Calculate how well resume matches job requirements"""
    score = 0
    max_score = 0
    
    # Skills matching (50% weight)
    resume_skills = set(skill.lower() for skill in parsed_resume.skills)
    job_skills = extract_skills_from_job(job.description)  # You need to implement this
    
    if job_skills:
        skill_match = len(resume_skills.intersection(job_skills)) / len(job_skills)
        score += skill_match * 0.5
        max_score += 0.5
    
    # Experience matching (30% weight)
    required_exp = extract_experience_requirement(job.description)  # Implement this
    if required_exp:
        exp_match = min(parsed_resume.years_experience / required_exp, 1.0)
        score += exp_match * 0.3
        max_score += 0.3
    
    # Education matching (20% weight)
    # Implement education requirement extraction
    
    return score / max_score if max_score > 0 else 0
def extract_skills_from_job(job_description):
    """Extract skills from job description text"""
    if not job_description:
        return []
    
    # Comprehensive skills database
    skill_categories = {
        'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala'],
        'web': ['html', 'css', 'react', 'angular', 'vue', 'django', 'flask', 'node.js', 'express', 'spring', 'laravel', 'asp.net'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra', 'dynamodb'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'ci/cd'],
        'tools': ['git', 'github', 'gitlab', 'jira', 'confluence', 'figma', 'photoshop', 'illustrator'],
        'data_science': ['python', 'r', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'data analysis'],
        'mobile': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
        'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'project management', 'agile', 'scrum']
    }
    
    found_skills = []
    description_lower = job_description.lower()
    
    for category, skills in skill_categories.items():
        for skill in skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', description_lower):
                found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates

def extract_experience_requirement(job_description):
    """Extract years of experience requirement from job description"""
    if not job_description:
        return 0
    
    # Patterns to find experience requirements
    patterns = [
        r'(\d+)[+\s]*(?:years?|yrs?)(?:\s*of?\s*experience)?',
        r'experience.*?(\d+)[+\s]*(?:years?|yrs?)',
        r'(\d+)[+\s]*(?:years?|yrs?).*?experience'
    ]
    
    description_lower = job_description.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, description_lower)
        if matches:
            # Return the highest experience requirement found
            return max(int(match) for match in matches)
    
    return 0  # Default if no experience requirement found

@login_required
def match_jobs(request, resume_id):
    """Find jobs that match a specific resume"""
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        parsed_data = ParsedResume.objects.get(resume=resume)
        
        # Get all jobs
        jobs = Job.objects.all()
        matched_jobs = []
        
        for job in jobs:
            match_score = calculate_job_match_for_resume(parsed_data, job)
            matched_skills = get_matched_skills(parsed_data.get_skills_list(), job)
            
            if match_score > 20:  # Only show jobs with >20% match
                matched_jobs.append({
                    'job': job,
                    'match_score': round(match_score, 1),
                    'matched_skills': matched_skills,
                    'missing_skills': get_missing_skills(parsed_data.get_skills_list(), job)
                })
        
        # Sort by match score (highest first)
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        context = {
            'resume': resume,
            'parsed_data': parsed_data,
            'matched_jobs': matched_jobs,
            'total_jobs_found': len(matched_jobs)
        }
        
        return render(request, 'job_matches.html', context)
        
    except (Resume.DoesNotExist, ParsedResume.DoesNotExist):
        messages.error(request, 'Resume not found or not analyzed yet.')
        return redirect('resume_list')

def calculate_job_match_for_resume(parsed_resume, job):
    """Calculate match score between resume and job"""
    score = 0
    max_score = 0
    
    # Extract job requirements
    job_skills = extract_skills_from_job(job.description)
    required_experience = extract_experience_requirement(job.description)
    
    # Skills matching (60% weight)
    resume_skills = parsed_resume.get_skills_list()
    if job_skills:
        matched_skills = set(resume_skills) & set(job_skills)
        skill_score = len(matched_skills) / len(job_skills) if job_skills else 0
        score += skill_score * 0.6
        max_score += 0.6
    
    # Experience matching (30% weight)
    if required_experience > 0:
        resume_experience = parsed_resume.years_experience or 0
        if resume_experience >= required_experience:
            exp_score = 1.0
        else:
            exp_score = resume_experience / required_experience
        score += exp_score * 0.3
        max_score += 0.3
    else:
        # If no experience requirement, give full points
        score += 0.3
        max_score += 0.3
    
    # Education level matching (10% weight)
    # Simple implementation - you can enhance this based on actual education requirements
    score += 0.1
    max_score += 0.1
    
    return (score / max_score) * 100 if max_score > 0 else 0

def get_matched_skills(resume_skills, job):
    """Get skills that match between resume and job"""
    job_skills = extract_skills_from_job(job.description)
    return list(set(resume_skills) & set(job_skills))

def get_missing_skills(resume_skills, job):
    """Get skills required by job but missing from resume"""
    job_skills = extract_skills_from_job(job.description)
    return list(set(job_skills) - set(resume_skills))