#!/bin/bash

# Test admin API endpoints
echo "=== Testing Admin API ==="

# Get admin token
echo "Getting admin token..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login-with-verification-check/" \
    -H "Content-Type: application/json" \
    -d '{"username_or_email": "admin", "password": "admin123"}')

TOKEN=$(echo "$RESPONSE" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('access', ''))")

if [ -z "$TOKEN" ]; then
    echo "Failed to get token. Response:"
    echo "$RESPONSE"
    exit 1
fi

echo "Token obtained successfully"

# Test admin users endpoint
echo "Testing admin users endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/admin/users/?page=1&page_size=5" | python3 -m json.tool

echo "=== Test completed ==="