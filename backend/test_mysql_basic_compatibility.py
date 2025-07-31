#!/usr/bin/env python
"""
Basic MySQL Compatibility Test

This test focuses on core database functionality without complex model dependencies.
"""

import os
import sys
import django
from django.test import TestCase
from django.db import connection
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

User = get_user_model()


class BasicMySQLTest(TestCase):
    """Basic MySQL functionality tests"""
    
    def test_mysql_connection(self):
        """Test basic MySQL connection"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_mysql_engine(self):
        """Verify MySQL engine is being used"""
        self.assertEqual(connection.vendor, 'mysql')
    
    def test_basic_user_operations(self):
        """Test basic user model operations"""
        # Create user
        user = User.objects.create_user(
            username='basictest',
            email='basic@test.com',
            password='testpass123'
        )
        
        # Verify creation
        self.assertIsNotNone(user.id)
        
        # Read user
        retrieved_user = User.objects.get(username='basictest')
        self.assertEqual(retrieved_user.email, 'basic@test.com')
        
        # Update user
        retrieved_user.first_name = 'Basic'
        retrieved_user.save()
        
        updated_user = User.objects.get(username='basictest')
        self.assertEqual(updated_user.first_name, 'Basic')
        
        # Delete user
        user_id = updated_user.id
        updated_user.delete()
        self.assertFalse(User.objects.filter(id=user_id).exists())
    
    def test_mysql_charset(self):
        """Test MySQL charset configuration"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@character_set_database")
            charset = cursor.fetchone()[0]
            self.assertIn('utf8', charset.lower())
    
    def test_mysql_sql_mode(self):
        """Test MySQL SQL mode configuration"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@sql_mode")
            sql_mode = cursor.fetchone()[0]
            # Should have strict mode enabled
            self.assertIn('STRICT_TRANS_TABLES', sql_mode)


if __name__ == '__main__':
    import unittest
    unittest.main()