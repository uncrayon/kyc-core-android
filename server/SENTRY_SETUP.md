# Sentry Setup Guide

## Problem

If you encounter the error:
```
ERROR: relation "sentry_option" does not exist at character 149
```

This means Sentry is trying to use the KYC application database (`kyc_db`) but hasn't been initialized with its own tables.

## Solution

The fix has been applied to [`docker-compose.yml`](docker-compose.yml:131) to use a separate `sentry_db` database for Sentry.

### Quick Fix Steps

1. **Stop all containers:**
   ```bash
   cd server
   docker-compose down
   ```

2. **Start the containers (db and redis must be running first):**
   ```bash
   docker-compose up -d db redis
   ```

3. **Initialize Sentry database (run the initialization script):**
   ```bash
   chmod +x scripts/init_sentry_db.sh
   ./scripts/init_sentry_db.sh
   ```

   Or manually run:
   ```bash
   # Create the sentry_db database
   docker-compose exec db psql -U kyc_user -d postgres -c "CREATE DATABASE sentry_db;"
   
   # Run Sentry migrations
   docker-compose run --rm sentry upgrade --noinput
   
   # Create Sentry superuser
   docker-compose run --rm sentry createuser --email admin@example.com --password admin --superuser
   ```

4. **Start all services:**
   ```bash
   docker-compose up -d
   ```

### Verify the Fix

Check that Sentry is running without errors:
```bash
docker-compose logs sentry | grep -i error
```

Access Sentry at: http://localhost:9003
- **Email:** admin@example.com
- **Password:** admin

## What Changed

- **Before:** Sentry used `kyc_db` (same as KYC application)
- **After:** Sentry uses `sentry_db` (separate database in same PostgreSQL instance)

This keeps both applications isolated while sharing the same database server.

## Optional: Disable Sentry

If you don't need Sentry monitoring, you can comment out or remove the `sentry` service from [`docker-compose.yml`](docker-compose.yml:123).