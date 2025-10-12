from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, Application, UserProfile
from .forms import JobForm, ApplicationForm, UserProfileForm
from django.db.models import Q

@login_required
def dashboard(request):
    # Get or create user profile
    UserProfile.objects.get_or_create(user=request.user)
    
    user_jobs = Job.objects.filter(posted_by=request.user)
    user_applications = Application.objects.filter(applicant=request.user)
    context = {
        'user_jobs': user_jobs,
        'user_applications': user_applications
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
    return render(request, 'jobs/my_applications.html', {'applications': applications})

@login_required
def manage_jobs(request):
    jobs = Job.objects.filter(posted_by=request.user).order_by('-date_posted')
    return render(request, 'jobs/manage_jobs.html', {'jobs': jobs})

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
            Q(company__icontains=search_query) |
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

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, 'jobs/job_detail.html', {'job': job})

@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('job_list')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})

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
            messages.success(request, 'Application submitted successfully!')
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

@login_required
def update_application_status(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        # Check if the current user is the job poster
        if application.job.posted_by != request.user:
            messages.error(request, 'You do not have permission to update this application.')
            return redirect('dashboard')
        
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            if notes:
                application.notes = notes
            application.save()
            messages.success(request, f'Application status updated to {dict(Application.STATUS_CHOICES)[new_status]}')
        else:
            messages.error(request, 'Invalid status selected.')
        
        return redirect('manage_job_applications', job_id=application.job.id)

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