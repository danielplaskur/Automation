#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('de-en.sqlite3')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(f"  {table[0]}")

# Check each table's structure
for table in tables:
    table_name = table[0]
    print(f"\nStructure of {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Show sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        print("  Sample data:")
        for row in rows:
            print(f"    {row}")

conn.close()
