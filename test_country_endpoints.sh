#!/bin/bash

# Test script for country API endpoints
# Usage: ./test_country_endpoints.sh

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "   Country API Endpoints Test Suite"
echo "=========================================="
echo ""

# Test 1: Get user location data
echo -e "${BLUE}Test 1: Get User Location Data${NC}"
echo "POST $BASE_URL/api/auth/location-data/"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/location-data/" \
  -H "Content-Type: application/json" \
  -d '{}')

if echo "$RESPONSE" | grep -q '"success": true'; then
  echo -e "${GREEN}✓ Location detection successful${NC}"
  COUNTRY=$(echo "$RESPONSE" | grep -o '"iso3": "[^"]*"' | head -1 | cut -d'"' -f4)
  echo "  Detected country: $COUNTRY"
else
  echo -e "${RED}✗ Location detection failed${NC}"
fi
echo ""

# Test 2: Get all countries
echo -e "${BLUE}Test 2: Get All Countries${NC}"
echo "GET $BASE_URL/api/auth/countries/phone-data/"
RESPONSE=$(curl -s "$BASE_URL/api/auth/countries/phone-data/")

if echo "$RESPONSE" | grep -q '"success": true'; then
  COUNT=$(echo "$RESPONSE" | grep -o '"count": [0-9]*' | cut -d' ' -f2)
  echo -e "${GREEN}✓ Retrieved $COUNT countries${NC}"
else
  echo -e "${RED}✗ Failed to get countries${NC}"
fi
echo ""

# Test 3: Search countries
echo -e "${BLUE}Test 3: Search Countries (query: 'can')${NC}"
echo "GET $BASE_URL/api/auth/countries/phone-data/?search=can"
RESPONSE=$(curl -s "$BASE_URL/api/auth/countries/phone-data/?search=can")

if echo "$RESPONSE" | grep -q '"success": true'; then
  COUNT=$(echo "$RESPONSE" | grep -o '"count": [0-9]*' | cut -d' ' -f2)
  echo -e "${GREEN}✓ Search returned $COUNT results${NC}"
  # Show first result
  if echo "$RESPONSE" | grep -q '"name"'; then
    NAME=$(echo "$RESPONSE" | grep -o '"name": "[^"]*"' | head -1 | cut -d'"' -f4)
    echo "  First result: $NAME"
  fi
else
  echo -e "${RED}✗ Search failed${NC}"
fi
echo ""

# Test 4: Filter by region
echo -e "${BLUE}Test 4: Filter by Region (West Africa)${NC}"
echo "GET $BASE_URL/api/auth/countries/phone-data/?region=West+Africa"
RESPONSE=$(curl -s "$BASE_URL/api/auth/countries/phone-data/?region=West+Africa")

if echo "$RESPONSE" | grep -q '"success": true'; then
  COUNT=$(echo "$RESPONSE" | grep -o '"count": [0-9]*' | cut -d' ' -f2)
  echo -e "${GREEN}✓ Found $COUNT countries in West Africa${NC}"
else
  echo -e "${RED}✗ Region filter failed${NC}"
fi
echo ""

# Test 5: Get specific country
echo -e "${BLUE}Test 5: Get Specific Country (BEN)${NC}"
echo "GET $BASE_URL/api/auth/countries/phone-data/?iso3=BEN"
RESPONSE=$(curl -s "$BASE_URL/api/auth/countries/phone-data/?iso3=BEN")

if echo "$RESPONSE" | grep -q '"success": true'; then
  if echo "$RESPONSE" | grep -q '"BEN"'; then
    echo -e "${GREEN}✓ Retrieved Benin${NC}"
    PHONE=$(echo "$RESPONSE" | grep -o '"phone_code": "[^"]*"' | head -1 | cut -d'"' -f4)
    echo "  Phone code: $PHONE"
  else
    echo -e "${RED}✗ Benin not found${NC}"
  fi
else
  echo -e "${RED}✗ Failed to get specific country${NC}"
fi
echo ""

# Test 6: Get all regions
echo -e "${BLUE}Test 6: Get All Regions${NC}"
echo "GET $BASE_URL/api/auth/countries/regions/"
RESPONSE=$(curl -s "$BASE_URL/api/auth/countries/regions/")

if echo "$RESPONSE" | grep -q '"success": true'; then
  COUNT=$(echo "$RESPONSE" | grep -o '"count": [0-9]*' | cut -d' ' -f2)
  echo -e "${GREEN}✓ Retrieved $COUNT regions${NC}"
else
  echo -e "${RED}✗ Failed to get regions${NC}"
fi
echo ""

echo "=========================================="
echo "   Test Suite Complete"
echo "=========================================="
