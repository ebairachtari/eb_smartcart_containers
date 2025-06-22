#!/bin/bash

# Χρώματα για output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Κάνουμε login...${NC}"


LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
        "email": "demo_user@unipi.gr",
        "password": "qqQQ11!!"
      }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo -e "${RED}Login failed. Response:${NC}"
  echo $LOGIN_RESPONSE
  exit 1
fi

echo -e "${GREEN}Login επιτυχές. Token:${NC} $TOKEN"

# Κλήση σε protected endpoint
echo -e "\n${GREEN}Δοκιμή /profile...${NC}"

curl -s -X GET http://localhost:5000/profile \
  -H "Authorization: Bearer $TOKEN"
