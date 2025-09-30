#!/bin/bash
# Script to initialize Sentry database

echo "Initializing Sentry database..."

# Step 1: Create the sentry_db database
echo "Step 1: Creating sentry_db database..."
docker-compose exec -T db psql -U kyc_user -d postgres -c "CREATE DATABASE sentry_db;"

if [ $? -eq 0 ]; then
    echo "✓ Database sentry_db created successfully"
else
    echo "⚠ Database may already exist or there was an error"
fi

# Step 2: Run Sentry database migrations
echo "Step 2: Running Sentry migrations (this may take a few minutes)..."
docker-compose run --rm sentry upgrade --noinput

if [ $? -eq 0 ]; then
    echo "✓ Sentry migrations completed successfully"
else
    echo "✗ Sentry migration failed"
    exit 1
fi

# Step 3: Create a superuser for Sentry
echo "Step 3: Creating Sentry superuser..."
echo "Default credentials: admin@example.com / admin"
docker-compose run --rm sentry createuser --email admin@example.com --password admin --superuser

if [ $? -eq 0 ]; then
    echo "✓ Sentry superuser created successfully"
    echo ""
    echo "=========================================="
    echo "Sentry initialization complete!"
    echo "Access Sentry at: http://localhost:9003"
    echo "Login: admin@example.com"
    echo "Password: admin"
    echo "=========================================="
else
    echo "✗ Failed to create Sentry superuser"
    exit 1
fi