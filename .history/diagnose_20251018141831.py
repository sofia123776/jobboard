import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobboard.settings')
django.setup()

from django.db import connection

def diagnose_database():
    print("=== Database Diagnosis ===")
    
    # Check if jobs_job table exists
    tables = connection.introspection.table_names()
    print(f"Tables in database: {tables}")
    
    if 'jobs_job' in tables:
        print("\n=== jobs_job table structure ===")
        with connection.cursor() as cursor:
            # Get table structure
            cursor.execute("DESCRIBE jobs_job")
            columns = cursor.fetchall()
            for column in columns:
                print(f"Column: {column[0]} | Type: {column[1]} | Null: {column[2]} | Key: {column[3]}")
            
            # Check for company_name duplicates
            company_cols = [col for col in columns if 'company' in col[0].lower()]
            print(f"\nCompany-related columns: {[col[0] for col in company_cols]}")
    
    print("\n=== Migration status ===")
    from django.db.migrations.recorder import MigrationRecorder
    applied_migrations = MigrationRecorder.Migration.objects.filter(app='jobs')
    print(f"Applied migrations for 'jobs' app:")
    for migration in applied_migrations:
        print(f"  - {migration.name}")

if __name__ == "__main__":
    diagnose_database()