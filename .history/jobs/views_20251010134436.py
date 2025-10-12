
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, Application, UserProfile
from .forms import JobForm, ApplicationForm, UserProfileForm

def home(request):
    # Get latest jobs for the home page (limit to 3 for featured section)
    latest_jobs = Job.objects.all().order_by('-date_posted')[:3]
    return render(request, 'jobs/home.html', {'latest_jobs': latest_jobs})

def job_list(request):
    # Get all jobs for the jobs listing page
    jobs = Job.objects.all().order_by('-date_posted')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

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
            return redirect('job_list')  # Redirect to job list after posting
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
            # Set the full_name and email from the user model
            application.full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            application.email = request.user.email
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = ApplicationForm()
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

@login_required
def dashboard(request):
    user_jobs = Job.objects.filter(posted_by=request.user)
    user_applications = Application.objects.filter(applicant=request.user)
    context = {
        'user_jobs': user_jobs,
        'user_applications': user_applications
    }
    return render(request, 'jobs/dashboard.html', context)

@login_required
def profile(request):
    profile = request.user.userprofile
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