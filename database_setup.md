# Database Setup and Troubleshooting Guide

## Current Issue
The application is failing to connect to PostgreSQL database even after creating the database.

## Root Cause Analysis
The database connection logic has two steps:
1. Basic PostgreSQL connection test (using psycopg2 directly)
2. SQLAlchemy engine creation and session test

The issue is likely in step 2 - the SQLAlchemy engine creation or session test.

## Solution Steps

### Step 1: Verify Database Exists
```bash
# Connect to PostgreSQL directly
psql -h localhost -U postgres -d xpanda_erp

# Check if database exists
\l xpanda_erp
```

### Step 2: Test Connection Manually
```bash
# Test basic connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='xpanda_erp',
        user='postgres',
        password='your_password'
    )
    print('Basic connection: SUCCESS')
    conn.close()
except Exception as e:
    print(f'Basic connection: FAILED - {e}')
"
```

### Step 3: Check PostgreSQL Service
```bash
# Windows
net start postgresql-x64-14

# Or check if running
sc query postgresql
```

### Step 4: Reset Database (if needed)
```bash
# Drop and recreate database
python utils/db_manager.py reset

# Or manual
psql -U postgres -c "DROP DATABASE IF EXISTS xpanda_erp;"
psql -U postgres -c "CREATE DATABASE xpanda_erp;"
```

### Step 5: Run Migrations
```bash
# Create and run initial migration
python utils/db_manager.py setup

# Or manually
python -m alembic revision --autogenerate -m "Initial schema"
python -m alembic upgrade head
```

## Common Issues and Solutions

### Issue: "Database does not exist"
**Solution**: Create database first
```sql
CREATE DATABASE xpanda_erp;
```

### Issue: "Authentication failed"
**Solution**: Check credentials
1. Verify password in .env file
2. Verify user exists: `\du` in psql
3. Check pg_hba.conf for authentication settings

### Issue: "Connection refused"
**Solution**: PostgreSQL service issues
1. Check if PostgreSQL is running
2. Check port (default: 5432)
3. Check firewall settings
4. Check postgresql.conf for listen_addresses

### Issue: "FATAL: database "xpanda_erp" does not exist"
**Solution**: The database wasn't created properly
```bash
# Connect as superuser and create
psql -U postgres
CREATE DATABASE xpanda_erp OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE xpanda_erp TO postgres;
```

## Quick Fix Command
```bash
# One command to fix most issues
python -c "
import psycopg2
import sys

try:
    # Test connection
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='xpanda_erp',
        user='postgres',
        password='your_password'
    )
    print('✅ Connection successful!')
    conn.close()
except psycopg2.OperationalError as e:
    print(f'❌ Connection failed: {e}')
    if 'does not exist' in str(e):
        print('💡 Solution: Create database first')
        print('   psql -U postgres -c \"CREATE DATABASE xpanda_erp;\"')
    elif 'authentication failed' in str(e).lower():
        print('💡 Solution: Check password in .env file')
        print('   DB_PASSWORD=your_actual_password')
    elif 'connection refused' in str(e).lower():
        print('💡 Solution: Check PostgreSQL service')
        print('   net start postgresql-x64-14')
    sys.exit(1)
"
```

## Environment Variables Check
```bash
# Verify .env file is loaded
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')
print(f'DB_PORT: {os.getenv(\"DB_PORT\")}')
print(f'DB_NAME: {os.getenv(\"DB_NAME\")}')
print(f'DB_USER: {os.getenv(\"DB_USER\")}')
print(f'DB_PASSWORD: {\"SET\" if os.getenv(\"DB_PASSWORD\") else \"NOT_SET\"}')
"
```
