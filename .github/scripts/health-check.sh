#!/bin/bash

##############################################################################
# Comprehensive Health Check Script
# 
# Performs thorough health checks on all services and reports status
##############################################################################

set -euo pipefail

# Configuration
HOST="${1:-localhost}"
MAX_RETRIES="${2:-3}"
RETRY_DELAY="${3:-5}"
TIMEOUT="${4:-10}"

# Service endpoints
FRONTEND_PORT=8000
API_PORT=5000
BO_PORT=3001

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   FirefighterAI Health Check          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Host: $HOST"
echo "Max retries: $MAX_RETRIES"
echo "Timeout: ${TIMEOUT}s"
echo ""

##############################################################################
# Function: check_endpoint
# Checks if an endpoint is responding correctly
##############################################################################
check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local check_content="${4:-false}"
    
    echo -n "┌─ Checking $name... "
    
    local attempt=1
    while [ $attempt -le $MAX_RETRIES ]; do
        # Perform request
        local start_time=$(date +%s%3N)
        local response=$(curl -s -w "\n%{http_code}\n%{time_total}" \
                             --max-time $TIMEOUT \
                             --connect-timeout 5 \
                             "$url" 2>/dev/null || echo -e "\n000\n0")
        local end_time=$(date +%s%3N)
        
        # Parse response
        local body=$(echo "$response" | head -n -2)
        local status=$(echo "$response" | tail -n 2 | head -n 1)
        local time_total=$(echo "$response" | tail -n 1)
        local response_time=$((end_time - start_time))
        
        # Check status
        if [ "$status" = "$expected_status" ]; then
            echo -e "${GREEN}✓${NC}"
            echo "│  Status: $status"
            echo "│  Response time: ${response_time}ms"
            
            # Check response time warning
            if [ $response_time -gt 5000 ]; then
                echo -e "│  ${YELLOW}⚠ Slow response (>5s)${NC}"
                WARNINGS=$((WARNINGS + 1))
            fi
            
            # Check content if requested
            if [ "$check_content" = "true" ] && [ -n "$body" ]; then
                if echo "$body" | jq . > /dev/null 2>&1; then
                    local service_status=$(echo "$body" | jq -r '.status // "unknown"')
                    echo "│  Service status: $service_status"
                    
                    if [ "$service_status" = "healthy" ] || [ "$service_status" = "ok" ]; then
                        echo -e "│  ${GREEN}Service reports healthy${NC}"
                    else
                        echo -e "│  ${YELLOW}Service status: $service_status${NC}"
                        WARNINGS=$((WARNINGS + 1))
                    fi
                fi
            fi
            
            echo "└─"
            PASSED=$((PASSED + 1))
            return 0
        fi
        
        # Retry logic
        if [ $attempt -lt $MAX_RETRIES ]; then
            echo -n "retry $attempt... "
            sleep $RETRY_DELAY
            attempt=$((attempt + 1))
        else
            echo -e "${RED}✗${NC}"
            echo "│  Status: $status (expected: $expected_status)"
            echo "│  Failed after $MAX_RETRIES attempts"
            echo "└─"
            FAILED=$((FAILED + 1))
            return 1
        fi
    done
}

##############################################################################
# Function: check_tcp_port
# Checks if a TCP port is open and accepting connections
##############################################################################
check_tcp_port() {
    local name="$1"
    local port="$2"
    
    echo -n "┌─ Checking $name port ($port)... "
    
    if timeout 5 bash -c "echo > /dev/tcp/$HOST/$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        echo "│  Port is open"
        echo "└─"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "│  Port is closed or unreachable"
        echo "└─"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

##############################################################################
# Function: check_docker_service
# Checks Docker service status (if running locally)
##############################################################################
check_docker_service() {
    local service_name="$1"
    
    if [ "$HOST" = "localhost" ] || [ "$HOST" = "127.0.0.1" ]; then
        echo -n "┌─ Checking Docker service: $service_name... "
        
        if docker ps --format '{{.Names}}' | grep -q "$service_name"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$service_name" 2>/dev/null)
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$service_name" 2>/dev/null || echo "none")
            
            if [ "$status" = "running" ]; then
                echo -e "${GREEN}✓${NC}"
                echo "│  Status: $status"
                if [ "$health" != "none" ]; then
                    echo "│  Health: $health"
                fi
                echo "└─"
                PASSED=$((PASSED + 1))
                return 0
            else
                echo -e "${RED}✗${NC}"
                echo "│  Status: $status"
                echo "└─"
                FAILED=$((FAILED + 1))
                return 1
            fi
        else
            echo -e "${YELLOW}⚠${NC}"
            echo "│  Service not found"
            echo "└─"
            WARNINGS=$((WARNINGS + 1))
            return 1
        fi
    fi
}

##############################################################################
# Main Health Checks
##############################################################################
echo -e "${BLUE}=== Service Endpoints ===${NC}"
echo ""

# Frontend Health Check
check_endpoint "Frontend" "http://$HOST:$FRONTEND_PORT/health" "200" true
check_tcp_port "Frontend" "$FRONTEND_PORT"

echo ""

# API Health Check
check_endpoint "API" "http://$HOST:$API_PORT/health" "200" true
check_endpoint "API Docs" "http://$HOST:$API_PORT/api/docs" "200" false
check_tcp_port "API" "$API_PORT"

echo ""

# BackOffice Health Check
check_endpoint "BackOffice" "http://$HOST:$BO_PORT/health" "200" true
check_tcp_port "BackOffice" "$BO_PORT"

echo ""

# Docker Services (if local)
if [ "$HOST" = "localhost" ] || [ "$HOST" = "127.0.0.1" ]; then
    echo -e "${BLUE}=== Docker Services ===${NC}"
    echo ""
    
    check_docker_service "firefighter-frontend"
    check_docker_service "firefighter-api"
    check_docker_service "firefighter-backoffice"
    check_docker_service "mongo"
    check_docker_service "redis"
    
    echo ""
fi

##############################################################################
# Additional Checks
##############################################################################
echo -e "${BLUE}=== Additional Checks ===${NC}"
echo ""

# Check MongoDB connectivity (through API)
echo -n "┌─ Checking Database connectivity... "
DB_CHECK=$(curl -s --max-time $TIMEOUT "http://$HOST:$API_PORT/api/health/database" 2>/dev/null || echo "error")
if echo "$DB_CHECK" | jq -e '.database.connected == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    echo "│  Database is connected"
    echo "└─"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC}"
    echo "│  Database connection failed"
    echo "└─"
    FAILED=$((FAILED + 1))
fi

echo ""

# Check Redis connectivity (if available)
echo -n "┌─ Checking Cache connectivity... "
CACHE_CHECK=$(curl -s --max-time $TIMEOUT "http://$HOST:$API_PORT/api/health/cache" 2>/dev/null || echo "error")
if echo "$CACHE_CHECK" | jq -e '.cache.connected == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    echo "│  Cache is connected"
    echo "└─"
    PASSED=$((PASSED + 1))
elif echo "$CACHE_CHECK" | grep -q "not configured" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC}"
    echo "│  Cache is not configured (optional)"
    echo "└─"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${YELLOW}⚠${NC}"
    echo "│  Cache connection check skipped or failed"
    echo "└─"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

##############################################################################
# Performance Tests
##############################################################################
echo -e "${BLUE}=== Performance Tests ===${NC}"
echo ""

# Test API response time
echo "┌─ API Performance Test (10 requests)"
TOTAL_TIME=0
REQUESTS=10
for i in $(seq 1 $REQUESTS); do
    START=$(date +%s%3N)
    curl -s --max-time $TIMEOUT "http://$HOST:$API_PORT/health" > /dev/null 2>&1
    END=$(date +%s%3N)
    TIME=$((END - START))
    TOTAL_TIME=$((TOTAL_TIME + TIME))
done
AVG_TIME=$((TOTAL_TIME / REQUESTS))
echo "│  Average response time: ${AVG_TIME}ms"

if [ $AVG_TIME -lt 1000 ]; then
    echo -e "│  ${GREEN}Excellent performance${NC}"
    PASSED=$((PASSED + 1))
elif [ $AVG_TIME -lt 3000 ]; then
    echo -e "│  ${GREEN}Good performance${NC}"
    PASSED=$((PASSED + 1))
elif [ $AVG_TIME -lt 5000 ]; then
    echo -e "│  ${YELLOW}Acceptable performance${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "│  ${RED}Poor performance${NC}"
    FAILED=$((FAILED + 1))
fi
echo "└─"

echo ""

##############################################################################
# Summary Report
##############################################################################
TOTAL=$((PASSED + FAILED + WARNINGS))

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Health Check Summary                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Passed:   $PASSED${NC}"
echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "${RED}✗ Failed:   $FAILED${NC}"
echo -e "─────────────────"
echo "  Total:    $TOTAL"
echo ""

# Overall status
if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ ALL SYSTEMS OPERATIONAL            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠ SYSTEM HEALTHY WITH WARNINGS      ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ✗ SYSTEM ISSUES DETECTED             ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    exit 1
fi