#!/usr/bin/env python3
"""
Comprehensive endpoint test script for InnovateSphere.
Tests all backend API routes and the frontend dev server.
"""
import json
import time
import random
import string
import urllib.request
import urllib.error
import urllib.parse
import ssl
import sys

# Disable SSL verification for local testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BACKEND_URL = "http://127.0.0.1:5000"
FRONTEND_URL = "http://localhost:3000"

# Test state
results = []
access_token = None
refresh_token = None
admin_token = None
test_user_email = None
test_user_password = "TestPass123!"
test_idea_id = None


def random_string(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def make_request(method, url, data=None, token=None, expect_status=None):
    """Make HTTP request and return (status_code, response_body_dict_or_str)."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        status = resp.status
        raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8") if e.fp else ""
    except Exception as e:
        return None, str(e)

    try:
        body_json = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        body_json = raw

    return status, body_json


def test(name, method, path, data=None, token=None, expect_status=None, base_url=None):
    """Run a single endpoint test."""
    url = (base_url or BACKEND_URL) + path
    status, body = make_request(method, url, data=data, token=token)

    passed = True
    reason = ""

    if status is None:
        passed = False
        reason = f"Connection error: {body}"
    elif expect_status and status != expect_status:
        passed = False
        reason = f"Expected {expect_status}, got {status}"
    elif expect_status is None and status and status >= 500:
        passed = False
        reason = f"Server error {status}"

    status_icon = "PASS" if passed else "FAIL"
    status_str = str(status) if status else "ERR"
    print(f"  [{status_icon}] {method:6s} {path:55s} -> {status_str:4s} {reason}")

    results.append({
        "name": name,
        "method": method,
        "path": path,
        "status": status,
        "passed": passed,
        "reason": reason,
        "body": body if not passed else None,
    })

    return status, body


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def main():
    global access_token, refresh_token, admin_token, test_user_email, test_idea_id

    print("=" * 70)
    print("  InnovateSphere - Comprehensive Endpoint Test Suite")
    print("=" * 70)

    # ================================================================
    section("1. FRONTEND DEV SERVER")
    # ================================================================
    try:
        req = urllib.request.Request(FRONTEND_URL, method="GET")
        resp = urllib.request.urlopen(req, timeout=10)
        status = resp.status
        content = resp.read().decode("utf-8")
        passed = status == 200 and ("<!DOCTYPE" in content or "<html" in content.lower() or "<div" in content)
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] GET    {'/ (frontend)':55s} -> {status}")
        results.append({"name": "Frontend index", "method": "GET", "path": "/", "status": status, "passed": passed, "reason": ""})
    except Exception as e:
        print(f"  [FAIL] GET    {'/ (frontend)':55s} -> ERR  {e}")
        results.append({"name": "Frontend index", "method": "GET", "path": "/", "status": None, "passed": False, "reason": str(e)})

    # ================================================================
    section("2. HEALTH & PLATFORM ENDPOINTS (Public)")
    # ================================================================
    test("Health check", "GET", "/api/health", expect_status=200)
    test("Pipeline version", "GET", "/api/ai/pipeline-version", expect_status=200)
    test("Domains list", "GET", "/api/domains", expect_status=200)

    # Legacy endpoints
    test("Legacy generate-idea (deprecated)", "POST", "/api/generate-idea",
         data={"prompt": "test"}, expect_status=410)

    # ================================================================
    section("3. PUBLIC ENDPOINTS (No Auth)")
    # ================================================================
    test("Public ideas list", "GET", "/api/public/ideas", expect_status=200)
    test("Public top ideas", "GET", "/api/public/top-ideas", expect_status=200)
    test("Public top domains", "GET", "/api/public/top-domains", expect_status=200)
    test("Public stats", "GET", "/api/public/stats", expect_status=200)

    # Try to get a public idea (may or may not have data)
    status, body = test("Public idea detail (id=1)", "GET", "/api/public/ideas/1")
    if status == 200 and isinstance(body, dict):
        test_idea_id = body.get("idea", {}).get("id") or body.get("id") or 1

    # If no idea found at id=1, try to find one from the list
    if test_idea_id is None:
        status2, body2 = make_request("GET", f"{BACKEND_URL}/api/public/ideas")
        if status2 == 200 and isinstance(body2, dict):
            ideas = body2.get("ideas", body2.get("results", []))
            if ideas:
                test_idea_id = ideas[0].get("id", 1)
                print(f"  [INFO] Found test idea id={test_idea_id} from public ideas list")
            else:
                print(f"  [INFO] No public ideas found - some idea tests will be skipped")
    else:
        print(f"  [INFO] Using test idea id={test_idea_id}")

    # ================================================================
    section("4. AUTHENTICATION ENDPOINTS")
    # ================================================================

    # Register a test user
    test_user_email = f"test_{random_string()}@test.com"
    status, body = test("Register new user", "POST", "/api/register",
                        data={
                            "email": test_user_email,
                            "username": f"testuser_{random_string()}",
                            "password": test_user_password,
                            "skill_level": "intermediate"
                        }, expect_status=201)
    if status == 201 and isinstance(body, dict):
        access_token = body.get("access_token")
        refresh_token = body.get("refresh_token")
        print(f"         -> Registered: {test_user_email}, got tokens")
    elif status == 429:
        print(f"         -> Rate limited, trying login with existing admin instead")

    # Test duplicate registration
    test("Register duplicate email", "POST", "/api/register",
         data={
             "email": test_user_email,
             "username": f"dup_{random_string()}",
             "password": test_user_password,
         }, expect_status=409)

    # Test registration validation
    test("Register missing fields", "POST", "/api/register",
         data={"email": ""}, expect_status=400)

    test("Register short password", "POST", "/api/register",
         data={"email": "x@x.com", "username": "testxyz", "password": "12"}, expect_status=400)

    # Login
    if access_token is None:
        # Try the admin account
        status, body = test("Login admin", "POST", "/api/login",
                            data={"email": "test@example.com", "password": "AdminPass123"})
        if status == 200 and isinstance(body, dict):
            access_token = body.get("access_token")
            refresh_token = body.get("refresh_token")
            admin_token = access_token
            print(f"         -> Logged in as admin, got tokens")

    # Login with test user
    status, body = test("Login test user", "POST", "/api/login",
                        data={"email": test_user_email, "password": test_user_password},
                        expect_status=200)
    if status == 200 and isinstance(body, dict):
        access_token = body.get("access_token")
        refresh_token = body.get("refresh_token")

    # Login with wrong password
    test("Login wrong password", "POST", "/api/login",
         data={"email": test_user_email, "password": "wrongpass"}, expect_status=401)

    # Login with missing fields
    test("Login missing fields", "POST", "/api/login",
         data={"email": "", "password": ""}, expect_status=400)

    # Token refresh
    if refresh_token:
        status, body = test("Token refresh", "POST", "/api/refresh", token=refresh_token, expect_status=200)
        if status == 200 and isinstance(body, dict):
            new_token = body.get("access_token")
            if new_token:
                access_token = new_token
                print(f"         -> Refreshed token successfully")

    # ================================================================
    section("5. AUTHENTICATED USER ENDPOINTS")
    # ================================================================

    if access_token:
        # My ideas
        test("My ideas list", "GET", "/api/ideas/mine", token=access_token, expect_status=200)

        # Ideas detail (authenticated)
        if test_idea_id:
            test(f"Idea detail (id={test_idea_id})", "GET", f"/api/ideas/{test_idea_id}",
                 token=access_token)
            test(f"Novelty explanation (id={test_idea_id})", "GET",
                 f"/api/ideas/{test_idea_id}/novelty-explanation", token=access_token)
            test(f"Idea reviews (id={test_idea_id})", "GET",
                 f"/api/ideas/{test_idea_id}/reviews", token=access_token)
            test(f"Idea feedbacks (id={test_idea_id})", "GET",
                 f"/api/ideas/{test_idea_id}/feedbacks", token=access_token)

            # Submit feedback
            test(f"Submit feedback (id={test_idea_id})", "POST",
                 f"/api/ideas/{test_idea_id}/feedback",
                 data={"feedback_type": "high_quality", "comment": "Test feedback from automated test"},
                 token=access_token)

            # Submit review
            test(f"Submit review (id={test_idea_id})", "POST",
                 f"/api/ideas/{test_idea_id}/review",
                 data={"rating": 4, "comment": "Test review from automated test"},
                 token=access_token)

        # Retrieval sources
        test("Retrieval sources", "POST", "/api/retrieval/sources",
             data={"query": "machine learning healthcare", "domain_id": 1},
             token=access_token)

        # Novelty analysis
        test("Novelty analyze", "POST", "/api/novelty/analyze",
             data={"description": "Using AI to predict weather patterns from satellite imagery", "domain": "AI"},
             token=access_token)

        # Legacy check_novelty (delegates to novelty analyze)
        test("Legacy check novelty", "POST", "/api/check_novelty",
             data={"description": "Blockchain for supply chain", "domain": "blockchain"},
             token=access_token)

        # Idea generation (this kicks off async job)
        status, body = test("Generate idea (start job)", "POST", "/api/ideas/generate",
                            data={"subject": "AI-powered automated code review for security vulnerabilities", "domain_id": 1},
                            token=access_token)
        job_id = None
        if status in (200, 201, 202) and isinstance(body, dict):
            job_id = body.get("job_id")
            if job_id:
                print(f"         -> Job ID: {job_id}")
                # Poll for status
                time.sleep(2)
                test(f"Generation status (job={job_id})", "GET",
                     f"/api/ideas/generate/{job_id}", token=access_token)
    else:
        print("  [SKIP] No access token available - skipping authenticated endpoints")

    # Test unauthenticated access to protected endpoints
    test("My ideas (no auth)", "GET", "/api/ideas/mine", expect_status=401)
    test("Generate idea (no auth)", "POST", "/api/ideas/generate",
         data={"subject": "test idea"}, expect_status=401)
    test("Retrieval (no auth)", "POST", "/api/retrieval/sources",
         data={"query": "test"}, expect_status=401)

    # ================================================================
    section("6. ADMIN ENDPOINTS")
    # ================================================================

    # Try to get admin token
    if admin_token is None:
        admin_creds = [
            ("test@example.com", "AdminPass123"),
            ("admin@example.com", "admin123"),
            ("admin@example.com", "AdminPass123"),
            ("admin@innovatesphere.com", "admin123"),
        ]
        for admin_email, admin_pass in admin_creds:
            status, body = make_request("POST", f"{BACKEND_URL}/api/login",
                                        data={"email": admin_email, "password": admin_pass})
            if status == 200 and isinstance(body, dict):
                admin_token = body.get("access_token")
                print(f"  [INFO] Logged in as admin ({admin_email}) for admin endpoint tests")
                break

    if admin_token:
        # Analytics KPIs
        test("Admin KPIs", "GET", "/api/analytics/admin/kpis", token=admin_token)
        test("Admin domains", "GET", "/api/admin/domains", token=admin_token)
        test("Admin trends", "GET", "/api/admin/trends", token=admin_token)
        test("Admin distributions", "GET", "/api/admin/distributions", token=admin_token)
        test("Admin user-domains", "GET", "/api/admin/user-domains", token=admin_token)
        test("Admin bias transparency", "GET", "/api/analytics/admin/bias-transparency",
             token=admin_token)

        # Admin idea management
        test("Admin quality review", "GET", "/api/admin/ideas/quality-review", token=admin_token)
        test("Admin abuse events", "GET", "/api/admin/abuse-events", token=admin_token)

        if test_idea_id:
            test(f"Admin idea detail (id={test_idea_id})", "GET",
                 f"/api/admin/ideas/{test_idea_id}", token=admin_token)
            test(f"Admin bias breakdown (id={test_idea_id})", "GET",
                 f"/api/admin/ideas/{test_idea_id}/bias-breakdown", token=admin_token)
            test(f"Admin generation trace (id={test_idea_id})", "GET",
                 f"/api/admin/ideas/{test_idea_id}/generation-trace", token=admin_token)

            # Admin verdict
            test(f"Admin verdict (id={test_idea_id})", "POST",
                 f"/api/admin/ideas/{test_idea_id}/verdict",
                 data={"verdict": "approved", "notes": "Test verdict"},
                 token=admin_token)

            # Toggle human-verified
            test(f"Admin human-verified (id={test_idea_id})", "POST",
                 f"/api/admin/ideas/{test_idea_id}/human-verified",
                 data={"human_verified": True},
                 token=admin_token)

        # Test admin endpoints with regular user token (should fail)
        if access_token and access_token != admin_token:
            test("Admin KPIs (non-admin)", "GET", "/api/analytics/admin/kpis",
                 token=access_token, expect_status=403)
    else:
        print("  [SKIP] No admin token available - skipping admin endpoints")
        print("         (Create admin user or check credentials)")

    # ================================================================
    section("7. LOGOUT")
    # ================================================================
    if access_token:
        test("Logout", "POST", "/api/logout", token=access_token, expect_status=200)
        # Verify token is revoked
        test("Access after logout", "GET", "/api/ideas/mine", token=access_token, expect_status=401)

    # ================================================================
    section("8. FRONTEND PROXY TEST")
    # ================================================================
    # Test that the frontend proxy correctly forwards API requests
    try:
        req = urllib.request.Request(f"{FRONTEND_URL}/api/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=10)
        status = resp.status
        content = json.loads(resp.read().decode("utf-8"))
        passed = status == 200 and content.get("status") == "ok"
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] GET    {'/api/health (via frontend proxy)':55s} -> {status}")
        results.append({"name": "Frontend proxy health", "method": "GET",
                        "path": "/api/health (via proxy)", "status": status, "passed": passed, "reason": ""})
    except Exception as e:
        print(f"  [FAIL] GET    {'/api/health (via frontend proxy)':55s} -> ERR {e}")
        results.append({"name": "Frontend proxy health", "method": "GET",
                        "path": "/api/health (via proxy)", "status": None, "passed": False, "reason": str(e)})

    # ================================================================
    section("RESULTS SUMMARY")
    # ================================================================
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])

    print(f"\n  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Rate:   {passed/total*100:.1f}%" if total > 0 else "  Rate:   N/A")

    if failed > 0:
        print(f"\n  Failed tests:")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['method']} {r['path']}: {r['reason']}")
                if r.get("body") and isinstance(r["body"], dict):
                    err_msg = r["body"].get("error") or r["body"].get("message") or r["body"].get("msg", "")
                    if err_msg:
                        print(f"      Response: {err_msg}")

    print(f"\n{'='*70}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
