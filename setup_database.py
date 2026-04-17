#!/usr/bin/env python3
"""
Quick database fix for XPanda ERP-Lite.
Creates database and user with proper error handling.
"""

import psycopg2
import sys


def main():
    print("XPanda ERP-Lite Database Fix")
    print("=" * 40)

    try:
        # Connect to PostgreSQL as postgres superuser
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='412638925'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Connected to PostgreSQL successfully")

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'xpanda_erp'")
        db_exists = cursor.fetchone()

        if db_exists:
            print("✅ Database 'xpanda_erp' already exists")
        else:
            print("Creating database 'xpanda_erp'...")
            cursor.execute("CREATE DATABASE xpanda_erp")
            print("✅ Database 'xpanda_erp' created successfully")

        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'postgres'")
        user_exists = cursor.fetchone()

        if user_exists:
            print("✅ User 'postgres' already exists")
        else:
            print("Creating user 'postgres'...")
            cursor.execute("CREATE USER postgres WITH SUPERUSER PASSWORD '412638925'")
            print("✅ User 'postgres' created successfully")

        # Grant privileges
        print("Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE xpanda_erp TO postgres")
        print("✅ Privileges granted successfully")

        cursor.close()
        conn.close()

        print()
        print("🎉 Database setup completed successfully!")
        print("You can now run: python main.py")
        print()

        return 0

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())