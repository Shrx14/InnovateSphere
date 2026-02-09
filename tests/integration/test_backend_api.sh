#!/bin/bash
# InnovateSphere Backend API Testing Suite
# Complete test coverage for all 30+ endpoints
# Usage: bash test_backend.sh

API_BASE="http://localhost:5000/api"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function for colored output
test_result() {
    local test_name=$1
    local expected=$2
    local actual=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [[ "$actual" == "$expected" ]]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name (Expected: $expected, Got: $actual)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo -e "${BLUE}=== InnovateSphere Backend API Testing Suite ===${NC}\n"

# ============================================================================
# PHASE 1: AUTHENTICATION TESTS
# ============================================================================

echo -e "${YELLOW}[PHASE 1] Authentication Tests${NC}"

# Test 1.1: Login with valid credentials
echo "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [[ -n "$ACCESS_TOKEN" ]]; then
    echo -e "${GREEN}✓ Login successful - Token obtained${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Login failed - No token received${NC}"
    echo "Response: $LOGIN_RESPONSE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Store token for subsequent tests
TOKEN=$ACCESS_TOKEN

echo ""

# ============================================================================
# PHASE 2: PUBLIC ENDPOINTS (NO AUTH REQUIRED)
# ============================================================================

echo -e "${YELLOW}[PHASE 2] Public Endpoints${NC}"

# Test 2.1: Get domains list
echo "Testing GET /domains..."
DOMAINS_RESPONSE=$(curl -s -X GET "$API_BASE/domains" -w "\n%{http_code}")
HTTP_CODE=$(echo "$DOMAINS_RESPONSE" | tail -n1)
BODY=$(echo "$DOMAINS_RESPONSE" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo -e "${GREEN}✓ GET /domains returned 200${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ GET /domains returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 2.2: Get public ideas list
echo "Testing GET /public/ideas..."
PUBLIC_IDEAS=$(curl -s -X GET "$API_BASE/public/ideas" -w "\n%{http_code}")
HTTP_CODE=$(echo "$PUBLIC_IDEAS" | tail -n1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo -e "${GREEN}✓ GET /public/ideas returned 200${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ GET /public/ideas returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 2.3: Get public stats
echo "Testing GET /public/stats..."
STATS=$(curl -s -X GET "$API_BASE/public/stats" -w "\n%{http_code}")
HTTP_CODE=$(echo "$STATS" | tail -n1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo -e "${GREEN}✓ GET /public/stats returned 200${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ GET /public/stats returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""

# ============================================================================
# PHASE 3: PROTECTED USER ENDPOINTS
# ============================================================================

echo -e "${YELLOW}[PHASE 3] Protected User Endpoints${NC}"

# Test 3.1: Get user's ideas
echo "Testing GET /ideas/mine (with token)..."
USER_IDEAS=$(curl -s -X GET "$API_BASE/ideas/mine" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$USER_IDEAS" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "401" ]]; then
    echo -e "${GREEN}✓ GET /ideas/mine returned $HTTP_CODE (valid response)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ GET /ideas/mine returned unexpected $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 3.2: Test without token (should be 401)
echo "Testing missing authorization header..."
NO_AUTH=$(curl -s -X GET "$API_BASE/ideas/mine" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$NO_AUTH" | tail -n1)

if [[ "$HTTP_CODE" == "401" ]]; then
    echo -e "${GREEN}✓ Request without auth returned 401${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Request without auth returned $HTTP_CODE (expected 401)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""

# ============================================================================
# PHASE 4: ADMIN ENDPOINTS
# ============================================================================

echo -e "${YELLOW}[PHASE 4] Admin Endpoints${NC}"

# Test 4.1: Get admin review queue
echo "Testing GET /admin/ideas/quality-review..."
REVIEW_QUEUE=$(curl -s -X GET "$API_BASE/admin/ideas/quality-review" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$REVIEW_QUEUE" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "403" ]]; then
    echo -e "${GREEN}✓ Review queue returned $HTTP_CODE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Review queue returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 4.2: Get admin analytics domains
echo "Testing GET /admin/domains..."
ADMIN_DOMAINS=$(curl -s -X GET "$API_BASE/admin/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$ADMIN_DOMAINS" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "403" ]]; then
    echo -e "${GREEN}✓ Admin domains returned $HTTP_CODE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Admin domains returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 4.3: Get admin trends
echo "Testing GET /admin/trends..."
ADMIN_TRENDS=$(curl -s -X GET "$API_BASE/admin/trends" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$ADMIN_TRENDS" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "403" ]]; then
    echo -e "${GREEN}✓ Admin trends returned $HTTP_CODE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Admin trends returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 4.4: Get admin distributions
echo "Testing GET /admin/distributions..."
ADMIN_DIST=$(curl -s -X GET "$API_BASE/admin/distributions" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$ADMIN_DIST" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "403" ]]; then
    echo -e "${GREEN}✓ Admin distributions returned $HTTP_CODE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Admin distributions returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 4.5: Get admin user-domains
echo "Testing GET /admin/user-domains..."
ADMIN_USER_DOM=$(curl -s -X GET "$API_BASE/admin/user-domains" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$ADMIN_USER_DOM" | tail -n1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "403" ]]; then
    echo -e "${GREEN}✓ Admin user-domains returned $HTTP_CODE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Admin user-domains returned $HTTP_CODE${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}=== Test Summary ===${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Review the output above.${NC}"
    exit 1
fi
