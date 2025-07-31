#!/usr/bin/env python3
"""
MySQL Database Setup Script
This script sets up the MySQL database for the ecommerce platform
"""
import os
import sys
import django
import mysql.connector
from mysql.connector import Error
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def create_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='root'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✓ Database 'ecommerce_db' created or already exists")
            
            # Create a dedicated user for the application (optional but recommended)
            try:
                cursor.execute("CREATE USER IF NOT EXISTS 'ecommerce_user'@'localhost' IDENTIFIED BY 'ecommerce_password'")
                cursor.execute("GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost'")
                cursor.execute("FLUSH PRIVILEGES")
                print("✓ Database user 'ecommerce_user' created with proper privileges")
            except Error as e:
                print(f"Note: User creation skipped - {e}")
            
            cursor.close()
            
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()
    
    return True

def run_migrations():
    """Run Django migrations"""
    try:
        print("Running Django migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

def populate_sample_data():
    """Populate the database with sample data"""
    try:
        print("Populating database with sample data...")
        execute_from_command_line(['manage.py', 'populate_sample_data'])
        print("✓ Sample data populated successfully")
        return True
    except Exception as e:
        print(f"Error populating sample data: {e}")
        return False

def create_superuser():
    """Create a superuser if it doesn't exist"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(email='admin@example.com').exists():
            print("Creating superuser...")
            execute_from_command_line([
                'manage.py', 'createsuperuser', 
                '--email', 'admin@example.com',
                '--noinput'
            ])
            
            # Set password for the superuser
            admin_user = User.objects.get(email='admin@example.com')
            admin_user.set_password('admin123')
            admin_user.save()
            print("✓ Superuser created: admin@example.com / admin123")
        else:
            print("✓ Superuser already exists")
        return True
    except Exception as e:
        print(f"Error creating superuser: {e}")
        return False

def verify_database_connection():
    """Verify that Django can connect to the database"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print("✓ Database connection verified")
            return True
    except Exception as e:
        print(f"Error verifying database connection: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up MySQL database for ecommerce platform...")
    print("=" * 60)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database")
        return False
    
    # Step 2: Verify connection
    if not verify_database_connection():
        print("❌ Failed to verify database connection")
        return False
    
    # Step 3: Run migrations
    if not run_migrations():
        print("❌ Failed to run migrations")
        return False
    
    # Step 4: Create superuser
    if not create_superuser():
        print("❌ Failed to create superuser")
        return False
    
    # Step 5: Populate sample data
    if not populate_sample_data():
        print("❌ Failed to populate sample data")
        return False
    
    print("=" * 60)
    print("🎉 MySQL database setup completed successfully!")
    print("\nDatabase Details:")
    print("- Host: 127.0.0.1:3307")
    print("- Database: ecommerce_db")
    print("- Admin User: admin@example.com / admin123")
    print("\nYou can now start the Django development server:")
    print("python manage.py runserver")
    
    return True

if __name__ == "__main__":
    main()