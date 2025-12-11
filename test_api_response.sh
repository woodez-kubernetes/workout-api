#!/bin/bash

echo "Testing API responses for proper data structure..."
echo

# Test 1: Health check
echo "1. Health Check:"
curl -s http://127.0.0.1:8000/api/health/ | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:8000/api/health/
echo
echo

# Test 2: Register a test user
echo "2. Registering test user..."
TIMESTAMP=$(date +%s)
REGISTER_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"apitest$TIMESTAMP\",\"email\":\"apitest$TIMESTAMP@example.com\",\"password\":\"TestPass123!\",\"password_confirm\":\"TestPass123!\"}")

TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Failed to get token. Response:"
  echo $REGISTER_RESPONSE
  exit 1
fi

echo "Token obtained: ${TOKEN:0:20}..."
echo
echo

# Test 3: Get profile (the fixed endpoint)
echo "3. GET /api/auth/profile/ (should work now):"
curl -s -X GET http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Token $TOKEN" | python3 -m json.tool 2>/dev/null || curl -s -X GET http://127.0.0.1:8000/api/auth/profile/ -H "Authorization: Token $TOKEN"
echo
echo

# Test 4: List workouts (should return empty array with proper structure)
echo "4. GET /api/workouts/ (check structure):"
curl -s -X GET http://127.0.0.1:8000/api/workouts/ \
  -H "Authorization: Token $TOKEN" | python3 -m json.tool 2>/dev/null || curl -s -X GET http://127.0.0.1:8000/api/workouts/ -H "Authorization: Token $TOKEN"
echo
echo

# Test 5: List sessions (check date field is present)
echo "5. GET /api/sessions/ (check date field):"
curl -s -X GET http://127.0.0.1:8000/api/sessions/ \
  -H "Authorization: Token $TOKEN" | python3 -m json.tool 2>/dev/null || curl -s -X GET http://127.0.0.1:8000/api/sessions/ -H "Authorization: Token $TOKEN"
echo
echo

echo "✅ All API tests completed!"
