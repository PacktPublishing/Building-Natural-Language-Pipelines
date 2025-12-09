#!/bin/bash

# Script to generate htpasswd file for nginx basic authentication
# This creates the authentication credentials for accessing the Hayhooks API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Hayhooks API Authentication Setup ===${NC}\n"

# Check if htpasswd is installed
if ! command -v htpasswd &> /dev/null; then
    echo -e "${YELLOW}htpasswd not found. Installing apache2-utils...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y apache2-utils
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install httpd
    else
        echo -e "${RED}Please install apache2-utils manually${NC}"
        exit 1
    fi
fi

# Create nginx directory if it doesn't exist
mkdir -p nginx

# Prompt for username and password
echo -e "${YELLOW}Enter username for API access:${NC}"
read -r USERNAME

echo -e "${YELLOW}Enter password:${NC}"
read -rs PASSWORD

# Generate htpasswd file
echo "$PASSWORD" | htpasswd -i -c nginx/.htpasswd "$USERNAME"

echo -e "\n${GREEN}✓ Authentication file created successfully!${NC}"
echo -e "${GREEN}✓ Location: nginx/.htpasswd${NC}"
echo -e "${GREEN}✓ Username: $USERNAME${NC}"
echo -e "\n${YELLOW}Keep this password secure. You'll need it to access the API.${NC}"
echo -e "\n${YELLOW}Example curl command with authentication:${NC}"
echo -e "curl -u ${USERNAME}:YOUR_PASSWORD http://localhost:8080/status"
