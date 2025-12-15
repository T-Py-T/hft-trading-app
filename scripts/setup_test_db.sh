#!/bin/bash
# scripts/setup_test_db.sh
# Setup PostgreSQL test database and create schema

set -e

echo "Setting up test database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
  if pg_isready -h localhost -U trading_user > /dev/null 2>&1; then
    echo "PostgreSQL is ready"
    break
  fi
  echo "Attempt $i/30 - PostgreSQL not ready yet, waiting..."
  sleep 1
done

# Create test database
echo "Creating test database..."
PGPASSWORD=trading_password psql -h localhost -U trading_user -d trading_db <<EOF
CREATE DATABASE trading_db_test;
EOF

echo "Test database setup complete!"
echo ""
echo "To run tests:"
echo "  cd hft-trading-platform"
echo "  python -m pytest tests/ -v"
