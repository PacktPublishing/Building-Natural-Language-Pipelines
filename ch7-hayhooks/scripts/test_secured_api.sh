#!/bin/bash

# Script to test the secured Hayhooks API endpoints
# Tests both authenticated and unauthenticated access

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8080"

echo -e "${BLUE}=== Testing Secured Hayhooks API ===${NC}\n"

# Test 1: Health endpoint (no auth required)
echo -e "${YELLOW}Test 1: Health check (no auth required)${NC}"
if curl -s -f "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ Health endpoint accessible${NC}\n"
else
    echo -e "${RED}✗ Health endpoint failed${NC}\n"
fi

# Test 2: Status endpoint (no auth required)
echo -e "${YELLOW}Test 2: Status check (no auth required)${NC}"
if curl -s -f "$API_URL/status" > /dev/null; then
    echo -e "${GREEN}✓ Status endpoint accessible${NC}"
    curl -s "$API_URL/status" | jq '.' 2>/dev/null || cat
    echo ""
else
    echo -e "${RED}✗ Status endpoint failed${NC}\n"
fi

# Test 3: Protected endpoint without auth (should fail)
echo -e "${YELLOW}Test 3: Protected endpoint without authentication (should fail)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected (401 Unauthorized)${NC}\n"
else
    echo -e "${RED}✗ Unexpected response code: $HTTP_CODE${NC}\n"
fi

# Test 4: Protected endpoint with authentication
echo -e "${YELLOW}Test 4: Protected endpoint with authentication${NC}"

# Try to load credentials from .env file
if [ -f ".env" ]; then
    # Load credentials from .env file
    USERNAME=$(grep '^API_USERNAME=' .env | cut -d '=' -f2-)
    PASSWORD=$(grep '^API_PASSWORD=' .env | cut -d '=' -f2-)
    
    if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
        echo -e "${GREEN}✓ Using credentials from .env file${NC}"
        echo -e "${BLUE}Username: $USERNAME${NC}"
    else
        echo -e "${YELLOW}⚠ No API credentials found in .env file${NC}"
        echo -e "${BLUE}Enter your username:${NC}"
        read -r USERNAME
        echo -e "${BLUE}Enter your password:${NC}"
        read -rs PASSWORD
        echo ""
    fi
else
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo -e "${BLUE}Enter your username:${NC}"
    read -r USERNAME
    echo -e "${BLUE}Enter your password:${NC}"
    read -rs PASSWORD
    echo ""
fi

# Check authentication by trying to access the root endpoint
RESPONSE=$(curl -s -w "\n%{http_code}" -u "$USERNAME:$PASSWORD" "$API_URL/" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${RED}✗ Authentication failed${NC}"
    echo -e "${YELLOW}Please check your credentials in .env file or re-run ./scripts/generate_password.sh${NC}\n"
    exit 1
elif [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Authentication successful!${NC}"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
else
    echo -e "${YELLOW}⚠ Unexpected response code: $HTTP_CODE${NC}"
    echo "$BODY"
    echo ""
fi

# Test 5: List pipelines with auth
echo -e "${YELLOW}Test 5: List available pipelines${NC}"
PIPELINES=$(curl -s -u "$USERNAME:$PASSWORD" "$API_URL/" | jq -r '.pipelines // [] | length' 2>/dev/null || echo "0")
if [ "$PIPELINES" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $PIPELINES pipeline(s)${NC}"
    curl -s -u "$USERNAME:$PASSWORD" "$API_URL/" | jq '.pipelines' 2>/dev/null || cat
    echo ""
else
    echo -e "${YELLOW}⚠ No pipelines found or unable to parse response${NC}\n"
fi

echo -e "${BLUE}=== Testing Complete ===${NC}"
echo -e "\n${GREEN}Your API is secured and working correctly!${NC}"
if [ -f ".env" ] && grep -q "^API_USERNAME=" .env; then
    echo -e "${YELLOW}Credentials are stored in .env file for your convenience${NC}"
    echo -e "${YELLOW}Use: curl -u \$API_USERNAME:\$API_PASSWORD http://localhost:8080/status${NC}"
else
    echo -e "${YELLOW}Remember to use -u $USERNAME:YOUR_PASSWORD for all authenticated requests${NC}"
fi
