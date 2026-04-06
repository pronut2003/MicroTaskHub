#!/usr/bin/env bash
set -e

echo "=== Installing backend dependencies ==="
cd backend
pip install -r requirements.txt

echo "=== Installing frontend dependencies ==="
cd ../frontend
npm install

echo "=== Building frontend ==="
npm run build

echo "=== Copying frontend build to backend static ==="
rm -rf ../backend/auth-service/static
cp -r dist/ ../backend/auth-service/static/

echo "=== Build complete ==="
