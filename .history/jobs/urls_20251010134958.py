from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/post/', views.post_job, name='post_job'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    
    # New URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('jobs/<int:job_id>/applications/', views.job_applications, name='job_applications'),
]