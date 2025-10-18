import schedule
import time
import os
import django
from django.core.management import call_command

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobboard.settings')
    django.setup()

def send_alerts():
    """Function to run the management command"""
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for job alerts...")
        call_command('send_job_alerts')
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Alert check completed")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error sending alerts: {e}")

def main():
    """Main function to run the scheduler"""
    print("Starting JobBoard Alert Scheduler...")
    print("This will check for new job alerts every hour.")
    print("Press Ctrl+C to stop the scheduler.")
    print("-" * 50)
    
    # Setup Django
    setup_django()
    
    # Schedule the job to run every hour
    schedule.every(1).hour.do(send_alerts)
    
    # Also run every 10 minutes for testing (optional)
    schedule.every(10).minutes.do(send_alerts)
    
    # Run immediately on startup
    send_alerts()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user. Goodbye!")
    except Exception as e:
        print(f"Scheduler crashed with error: {e}")