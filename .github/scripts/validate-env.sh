#!/bin/bash

##############################################################################
# Environment Variables Validation Script
# 
# This script validates that all required environment variables and secrets
# are properly configured before deployment.
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
SUCCESS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Environment Validation Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

##############################################################################
# Function: check_variable
# Validates if a variable exists and optionally checks its format
##############################################################################
check_variable() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    local required="${2:-true}"
    local pattern="${3:-}"
    local description="${4:-$var_name}"
    
    echo -n "Checking $description... "
    
    if [ -z "$var_value" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}MISSING${NC}"
            ERRORS=$((ERRORS + 1))
            return 1
        else
            echo -e "${YELLOW}OPTIONAL (not set)${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 0
        fi
    fi
    
    # Check pattern if provided
    if [ -n "$pattern" ]; then
        if [[ ! $var_value =~ $pattern ]]; then
            echo -e "${RED}INVALID FORMAT${NC}"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    fi
    
    # Check length (basic security check)
    if [ ${#var_value} -lt 8 ] && [[ $var_name == *"KEY"* || $var_name == *"SECRET"* || $var_name == *"PASSWORD"* ]]; then
        echo -e "${YELLOW}TOO SHORT (security warning)${NC}"
        WARNINGS=$((WARNINGS + 1))
        return 0
    fi
    
    echo -e "${GREEN}OK${NC}"
    SUCCESS=$((SUCCESS + 1))
    return 0
}

##############################################################################
# Required Variables
##############################################################################
echo -e "\n${BLUE}=== Required Variables ===${NC}\n"

# MongoDB
check_variable "MONGODB_URI" true '^mongodb.*' "MongoDB URI"

# JWT Secrets
check_variable "JWT_SECRET_KEY" true '' "JWT Secret Key"
check_variable "SESSION_SECRET_KEY" true '' "Session Secret Key"
check_variable "BO_SESSION_SECRET" true '' "BackOffice Session Secret"

# Email Service
check_variable "SENDGRID_API_KEY" true '^SG\.' "SendGrid API Key"
check_variable "SENDGRID_FROM_EMAIL" true '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' "SendGrid From Email"

# AI Service
check_variable "ANTHROPIC_API_KEY" true '^sk-ant-' "Anthropic API Key"

# Server Configuration
check_variable "DIGITALOCEAN_HOST" true '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$|^[a-zA-Z0-9.-]+$' "DigitalOcean Host"
check_variable "DIGITALOCEAN_SSH_KEY" true '' "DigitalOcean SSH Key"

##############################################################################
# Optional Variables
##############################################################################
echo -e "\n${BLUE}=== Optional Variables ===${NC}\n"

check_variable "FRONTEND_URL" false '^https?://' "Frontend URL"
check_variable "API_URL" false '^https?://' "API URL"
check_variable "BO_URL" false '^https?://' "BackOffice URL"

check_variable "REDIS_URL" false '^redis://' "Redis URL"
check_variable "SENTRY_DSN" false '' "Sentry DSN"

##############################################################################
# Docker Registry Variables
##############################################################################
echo -e "\n${BLUE}=== Docker Registry ===${NC}\n"

check_variable "REGISTRY" false '' "Docker Registry"
check_variable "IMAGE_PREFIX" false '' "Image Prefix"
check_variable "IMAGE_TAG" false '' "Image Tag"

##############################################################################
# Security Checks
##############################################################################
echo -e "\n${BLUE}=== Security Checks ===${NC}\n"

# Check if secrets are using default/weak values
check_weak_secret() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    
    if [ -z "$var_value" ]; then
        return 0
    fi
    
    # List of weak/default values
    local weak_values=(
        "secret"
        "password"
        "12345"
        "admin"
        "test"
        "default"
        "changeme"
        "example"
    )
    
    local var_lower=$(echo "$var_value" | tr '[:upper:]' '[:lower:]')
    
    for weak in "${weak_values[@]}"; do
        if [[ $var_lower == *"$weak"* ]]; then
            echo -e "⚠️  ${YELLOW}WARNING: $var_name might contain weak value${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 1
        fi
    done
    
    return 0
}

check_weak_secret "JWT_SECRET_KEY"
check_weak_secret "SESSION_SECRET_KEY"
check_weak_secret "BO_SESSION_SECRET"

# Check for suspicious patterns in SSH key
if [ -n "${DIGITALOCEAN_SSH_KEY:-}" ]; then
    if [[ "${DIGITALOCEAN_SSH_KEY}" == *"PRIVATE KEY"* ]]; then
        echo -e "✅ ${GREEN}SSH Key format looks valid${NC}"
    else
        echo -e "⚠️  ${YELLOW}WARNING: SSH Key format might be invalid${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

##############################################################################
# Connectivity Checks (if in deployed environment)
##############################################################################
if [ "${CI:-false}" != "true" ] && [ -n "${DIGITALOCEAN_HOST:-}" ]; then
    echo -e "\n${BLUE}=== Connectivity Checks ===${NC}\n"
    
    # Check if host is reachable
    echo -n "Checking host connectivity... "
    if ping -c 1 -W 2 "$DIGITALOCEAN_HOST" &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${YELLOW}UNREACHABLE (might be expected)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Check MongoDB connectivity (if URI is accessible)
    if [ -n "${MONGODB_URI:-}" ]; then
        echo -n "Checking MongoDB connectivity... "
        # Extract host from MongoDB URI
        MONGO_HOST=$(echo "$MONGODB_URI" | sed -n 's|.*@\([^/]*\)/.*|\1|p')
        if [ -n "$MONGO_HOST" ]; then
            if nc -z -w 2 "$MONGO_HOST" 27017 &> /dev/null; then
                echo -e "${GREEN}OK${NC}"
                SUCCESS=$((SUCCESS + 1))
            else
                echo -e "${YELLOW}UNREACHABLE (might use different port or be firewalled)${NC}"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            echo -e "${YELLOW}SKIPPED (cannot parse host)${NC}"
        fi
    fi
fi

##############################################################################
# File Checks
##############################################################################
echo -e "\n${BLUE}=== File Checks ===${NC}\n"

# Check if required files exist
check_file() {
    local file="$1"
    local description="$2"
    
    echo -n "Checking $description... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}EXISTS${NC}"
        SUCCESS=$((SUCCESS + 1))
        return 0
    else
        echo -e "${YELLOW}NOT FOUND${NC}"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

check_file "docker-compose.yml" "docker-compose.yml"
check_file "docker-compose_prod.yml" "docker-compose_prod.yml"
check_file ".env.production" ".env.production template"

##############################################################################
# Summary
##############################################################################
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Success: $SUCCESS${NC}"
echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "${RED}✗ Errors: $ERRORS${NC}"
echo ""

##############################################################################
# Exit Status
##############################################################################
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Validation FAILED - Please fix errors before deployment${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation passed with warnings${NC}"
    exit 0
else
    echo -e "${GREEN}✅ Validation SUCCESSFUL - All checks passed${NC}"
    exit 0
fi