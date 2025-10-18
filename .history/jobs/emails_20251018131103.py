from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

def send_new_application_email(application):
    """Send email to employer when someone applies to their job"""
    employer = application.job.posted_by
    job = application.job
    
    subject = f"New Application for {job.title}"
    
    context = {
        'employer_name': employer.get_full_name() or employer.username,
        'job_title': job.title,
        'applicant_name': application.full_name,
        'applicant_email': application.email,
        'application_date': application.date_applied.strftime("%B %d, %Y"),
        'cover_letter_preview': application.cover_letter,
        'application_url': settings.SITE_URL + reverse('view_application_detail', args=[application.id]),
    }
    
    html_message = render_to_string('emails/new_application.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[employer.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    # Attach resume if needed
    if application.resume:
        email.attach_file(application.resume.path)
    
    email.send()

def send_application_status_email(application, old_status):
    """Send email to applicant when their application status changes"""
    if application.status == old_status:
        return  # No change
    
    applicant = application.applicant
    job = application.job
    
    subject = f"Application Update: {job.title}"
    
    context = {
        'applicant_name': application.full_name,
        'job_title': job.title,
        'company_name': job.company_name,
        'new_status': application.status,
        'status_display': application.get_status_display(),
        'update_date': application.date_applied.strftime("%B %d, %Y"),
        'application_url': settings.SITE_URL + reverse('view_application_detail', args=[application.id]),
        'job_url': settings.SITE_URL + reverse('job_detail', args=[job.id]),
    }
    
    html_message = render_to_string('emails/application_status_update.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[application.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send()

def send_job_alert_email(alert, matching_jobs):
    """Send email with new job matches for a job alert"""
    if not matching_jobs:
        return
    
    user = alert.user
    
    subject = f"New Jobs Matching Your Alert: {alert.name}"
    
    context = {
        'user_name': user.get_full_name() or user.username,
        'alert_name': alert.name,
        'jobs_count': len(matching_jobs),
        'jobs': matching_jobs[:5],  # Limit to 5 jobs in email
        'alert_management_url': settings.SITE_URL + reverse('job_alerts'),
        'browse_jobs_url': settings.SITE_URL + reverse('job_list'),
        'unsubscribe_url': settings.SITE_URL + reverse('toggle_job_alert', args=[alert.id]),
    }
    
    html_message = render_to_string('emails/job_alert_matches.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send()
    
    # Update last_sent timestamp
    from django.utils import timezone
    alert.last_sent = timezone.now()
    alert.save()