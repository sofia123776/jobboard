from django.urls import path
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/post/', views.post_job, name='post_job'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('jobs/<int:job_id>/applications/', views.job_applications, name='job_applications'),

    
    # Application Management URLs
    path('jobs/<int:job_id>/applications/', views.manage_job_applications, name='manage_job_applications'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:application_id>/', views.view_application_detail, name='view_application_detail'),

    # Job Alert URLs
    path('alerts/', views.job_alerts, name='job_alerts'),
    path('alerts/create/', views.create_job_alert, name='create_job_alert'),
    path('alerts/<int:alert_id>/edit/', views.edit_job_alert, name='edit_job_alert'),
    path('alerts/<int:alert_id>/toggle/', views.toggle_job_alert, name='toggle_job_alert'),
    path('alerts/<int:alert_id>/delete/', views.delete_job_alert, name='delete_job_alert'),
    path('alerts/<int:alert_id>/matches/', views.view_alert_matches, name='view_alert_matches'),

    # Company URLs
    path('companies/', views.company_list, name='company_list'),
    path('companies/my-companies/', views.my_companies, name='my_companies'),
    path('companies/create/', views.create_company, name='create_company'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<int:company_id>/edit/', views.edit_company, name='edit_company'),


    path('upload_resume/', views.upload_resume, name='upload_resume'),
    path('resumes/', views.resume_list, name='resume_list'),
    path('resume-analysis/<uuid:resume_id>/', views.resume_analysis, name='resume_analysis'),
    path('analyze-resume/', views.analyze_resume, name='analyze_resume'), 

     # Profile and networking URLs
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('profile/<str:username>/connections/', views.connections_list, name='connections_list'),
    path('network/suggestions/', views.network_suggestions, name='network_suggestions'),
]