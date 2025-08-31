#!/usr/bin/env python3
"""
Database Setup Script for QA Testing Framework

This script helps set up MySQL database for the QA testing framework.
It creates the necessary databases and users for different environments.
"""

import sys
import argparse
import mysql.connector
from mysql.connector import Error as MySQLError
from pathlib import Path

# Add the parent directory to the path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.interfaces import Environment
from core.database import DatabaseManager


def create_mysql_user_and_database(host="localhost", port=3307, root_password="", 
                                 db_name="qa_test_development", 
                                 db_user="qa_user", db_password="qa_password"):
    """Create MySQL user and database for QA testing"""
    
    try:
        # Connect as root to create user and database
        root_connection = mysql.connector.connect(
            host=host,
            port=port,
            user="root",
            password=root_password
        )
        
        cursor = root_connection.cursor()
        
        print(f"Connected to MySQL server at {host}:{port}")
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Created database: {db_name}")
        
        # Create user
        cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}'")
        print(f"Created user: {db_user}")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        print(f"Granted privileges to {db_user} on {db_name}")
        
        cursor.close()
        root_connection.close()
        
        return True
        
    except MySQLError as e:
        print(f"Error setting up MySQL: {e}")
        return False


def setup_test_schema(environment=Environment.DEVELOPMENT):
    """Setup test schema using DatabaseManager"""
    
    try:
        db_manager = DatabaseManager(environment)
        
        print(f"Setting up test schema for {environment.value} environment...")
        
        # Create database if it doesn't exist
        if db_manager.create_database():
            print(f"Database {db_manager.database} is ready")
        else:
            print(f"Failed to create database {db_manager.database}")
            return False
        
        # Setup test schema
        if db_manager.setup_test_schema():
            print("Test schema setup completed successfully")
            return True
        else:
            print("Failed to setup test schema")
            return False
            
    except Exception as e:
        print(f"Error setting up test schema: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup MySQL database for QA testing framework")
    parser.add_argument("--host", default="localhost", help="MySQL host (default: localhost)")
    parser.add_argument("--port", type=int, default=3307, help="MySQL port (default: 3307)")
    parser.add_argument("--root-password", default="", help="MySQL root password")
    parser.add_argument("--environment", choices=["development", "staging", "production"], 
                       default="development", help="Environment to setup (default: development)")
    parser.add_argument("--create-user", action="store_true", 
                       help="Create MySQL user and database (requires root access)")
    parser.add_argument("--setup-schema", action="store_true", 
                       help="Setup test schema in existing database")
    
    args = parser.parse_args()
    
    if not args.create_user and not args.setup_schema:
        print("Please specify --create-user and/or --setup-schema")
        return 1
    
    environment = Environment(args.environment.upper())
    
    success = True
    
    if args.create_user:
        print("Creating MySQL user and database...")
        
        # Database names for different environments
        db_names = {
            Environment.DEVELOPMENT: "qa_test_development",
            Environment.STAGING: "qa_test_staging", 
            Environment.PRODUCTION: "qa_test_production"
        }
        
        db_name = db_names.get(environment, "qa_test_development")
        
        if not create_mysql_user_and_database(
            host=args.host,
            port=args.port,
            root_password=args.root_password,
            db_name=db_name
        ):
            success = False
    
    if args.setup_schema and success:
        print("Setting up test schema...")
        if not setup_test_schema(environment):
            success = False
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print(f"\nYou can now run tests with the {environment.value} environment.")
        print("\nExample usage:")
        print("  python -m pytest tests/test_database.py -v")
        return 0
    else:
        print("\n❌ Database setup failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())