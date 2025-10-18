from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import JobAlert
from jobs.emails import send_job_alert_email

class Command(BaseCommand):
    help = 'Send job alert emails to users'
    
    def handle(self, *args, **options):
        alerts = JobAlert.objects.filter(is_active=True)
        
        for alert in alerts:
            # Check if it's time to send based on frequency
            if self.should_send_alert(alert):
                matching_jobs = alert.get_matching_jobs()
                if matching_jobs.exists():
                    try:
                        send_job_alert_email(alert, list(matching_jobs))
                        self.stdout.write(
                            self.style.SUCCESS(f'Sent alert to {alert.user.username} with {matching_jobs.count()} jobs')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to send alert to {alert.user.username}: {str(e)}')
                        )
    
    def should_send_alert(self, alert):
        if not alert.last_sent:
            return True
        
        now = timezone.now()
        time_since_last = now - alert.last_sent
        
        if alert.frequency == 'instant':
            return True
        elif alert.frequency == 'daily':
            return time_since_last.days >= 1
        elif alert.frequency == 'weekly':
            return time_since_last.days >= 7
        
        return False