#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute('DESCRIBE auth_user')

print("auth_user table structure:")
print("Field | Type | Null | Key | Default | Extra")
print("-" * 60)
for row in cursor.fetchall():
    print(" | ".join(str(col) for col in row))