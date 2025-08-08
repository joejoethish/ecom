#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SHOW TABLES LIKE 'supplier%'")
tables = cursor.fetchall()

print("Supplier tables found:")
for table in tables:
    print(f"  - {table[0]}")

if not tables:
    print("No supplier tables found!")
    print("\nAll tables:")
    cursor.execute("SHOW TABLES")
    all_tables = cursor.fetchall()
    for table in all_tables:
        print(f"  - {table[0]}")