"""
Comprehensive route + feature smoke-test for InnovateSphere.
Tests all public, user-authenticated, and admin-authenticated routes,
plus idea generation and novelty checking end-to-end.
"""

import json
import os
import time
import sys
import requests

BASE = "http://localhost:5000"
TIMEOUT = 60

# ── helpers ────────────────────────────────────────────────────────────────

class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    BOLD = "\033[1m"
    END = "\033[0m"

pass_count = 0
fail_count = 0
warn_count = 0
failures = []

def report(label, status_code, expected, extra=""):
    global pass_count, fail_count, warn_count
    ok = status_code in (expected if isinstance(expected, (list, tuple)) else [expected])
    tag = f"{Colors.OK}PASS{Colors.END}" if ok else f"{Colors.FAIL}FAIL{Colors.END}"
    if ok:
        pass_count += 1
    else:
        fail_count += 1
        failures.append((label, status_code, expected, extra))
    ex = f"  {extra}" if extra else ""
    print(f"  [{tag}] {label:55s}  => {status_code} (expect {expected}){ex}")


def get(url, headers=None, expect=200):
    try:
        r = requests.get(f"{BASE}{url}", headers=headers, timeout=TIMEOUT)
        report(f"GET {url}", r.status_code, expect, r.text[:120] if r.status_code not in ([expect] if isinstance(expect, int) else expect) else "")
        return r
    except Exception as e:
        report(f"GET {url}", 0, expect, str(e))
        return None


def post(url, data=None, headers=None, expect=200):
    try:
        r = requests.post(f"{BASE}{url}", json=data, headers=headers, timeout=TIMEOUT)
        report(f"POST {url}", r.status_code, expect, r.text[:120] if r.status_code not in ([expect] if isinstance(expect, int) else expect) else "")
        return r
    except Exception as e:
        report(f"POST {url}", 0, expect, str(e))
        return None


def login(email, password):
    r = requests.post(f"{BASE}/api/login", json={"email": email, "password": password}, timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        return data.get("access_token"), data.get("refresh_token")
    return None, None


def auth_header(token):
    return {"Authorization": f"Bearer {token}"} if token else {}


# ── 1. PUBLIC ROUTES (no auth) ────────────────────────────────────────────

def test_public_routes():
    print(f"\n{Colors.BOLD}═══ PUBLIC ROUTES (no auth) ═══{Colors.END}")
    get("/api/health")
    get("/api/public/ideas")
    get("/api/public/ideas?page=1&limit=5")
    get("/api/public/top-ideas")
    get("/api/public/top-domains")
    get("/api/public/stats")
    get("/api/domains")
    get("/api/ai/pipeline-version")
    # Public idea detail — use id=1 (may or may not exist)
    get("/api/public/ideas/1", expect=[200, 404])
    # Auth endpoints
    post("/api/login", {"email": "bad@bad.com", "password": "wrong"}, expect=401)


# ── 2. USER AUTH ──────────────────────────────────────────────────────────

def test_user_routes():
    print(f"\n{Colors.BOLD}═══ USER AUTH ROUTES ═══{Colors.END}")

    # Try logging in with known user credentials first
    user_email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    user_pass = os.getenv("TEST_USER_PASSWORD", "TestUser@123")
    token, refresh = login(user_email, user_pass)
    if token:
        print(f"  Logged in as existing user: {user_email}")
        h = auth_header(token)
        rh = auth_header(refresh)
        post("/api/refresh", headers=rh, expect=200)
    else:
        # Register a fresh user for this test run
        ts = int(time.time())
        email = f"routetest{ts}@test.com"
        reg_data = {
            "email": email,
            "username": f"routetest{ts}",
            "password": "TestPass123",
            "skill_level": "intermediate"
        }
        r = post("/api/register", reg_data, expect=201)
        if not r or r.status_code != 201:
            print(f"  {Colors.FAIL}Cannot proceed — registration failed{Colors.END}")
            return None, None

        token = r.json().get("access_token")
        refresh = r.json().get("refresh_token")
        h = auth_header(token)

        # Token refresh
        rh = auth_header(refresh)
        post("/api/refresh", headers=rh, expect=200)

    # Authenticated GETs
    get("/api/ideas/mine", headers=h)
    get("/api/domains", headers=h)

    # Trying to access admin routes with user token should 403
    get("/api/admin/ideas/quality-review", headers=h, expect=403)
    get("/api/analytics/admin/kpis", headers=h, expect=403)
    get("/api/admin/abuse-events", headers=h, expect=403)
    get("/api/admin/domains", headers=h, expect=403)
    get("/api/admin/trends", headers=h, expect=403)
    get("/api/admin/distributions", headers=h, expect=403)
    get("/api/admin/user-domains", headers=h, expect=403)
    get("/api/analytics/admin/bias-transparency", headers=h, expect=403)

    # Idea detail / reviews / feedbacks for non-existent idea
    get("/api/ideas/99999", headers=h, expect=404)
    get("/api/ideas/99999/reviews", headers=h, expect=[200, 404])
    get("/api/ideas/99999/feedbacks", headers=h, expect=[200, 404])

    # Logout
    post("/api/logout", headers=h, expect=200)

    # After logout, token should be revoked
    get("/api/ideas/mine", headers=h, expect=401)

    return user_email, token


# ── 3. ADMIN AUTH ─────────────────────────────────────────────────────────

def ensure_admin_user():
    """Try known admin credentials (loaded from env vars with defaults)."""
    admin_email = os.getenv("TEST_ADMIN_EMAIL")
    admin_pass = os.getenv("TEST_ADMIN_PASSWORD")
    if admin_email and admin_pass:
        token, _ = login(admin_email, admin_pass)
        if token:
            return admin_email, admin_pass, token
    for email, pw in [
        ("admin1@example.com", "Admin@123"),
        ("test@example.com", "AdminPass123"),
        ("admin@example.com", "admin123"),
    ]:
        token, _ = login(email, pw)
        if token:
            return email, pw, token
    return None, None, None


def test_admin_routes():
    print(f"\n{Colors.BOLD}═══ ADMIN AUTH ROUTES ═══{Colors.END}")

    admin_email, admin_pass, token = ensure_admin_user()
    if not token:
        global warn_count
        warn_count += 1
        print(f"  {Colors.WARN}No admin user available — will create one via direct API{Colors.END}")
        # Register a user and try to use it — admin routes should return 403
        # We still test that 403 is properly enforced
        ts = int(time.time())
        r = requests.post(f"{BASE}/api/register", json={
            "email": f"admincheck{ts}@test.com",
            "username": f"admincheck{ts}",
            "password": "TestPass123",
            "skill_level": "advanced"
        }, timeout=TIMEOUT)
        if r.status_code == 201:
            nonadmin_token = r.json().get("access_token")
            h = auth_header(nonadmin_token)
            print(f"  Testing admin routes return 403 for non-admin user:")
            get("/api/admin/ideas/quality-review", headers=h, expect=403)
            get("/api/analytics/admin/kpis", headers=h, expect=403)
            get("/api/admin/abuse-events", headers=h, expect=403)
        return

    report("POST /api/login (admin)", 200, 200)
    h = auth_header(token)

    # Admin GETs
    get("/api/admin/ideas/quality-review", headers=h)
    get("/api/admin/abuse-events", headers=h)
    get("/api/analytics/admin/kpis", headers=h)
    get("/api/admin/domains", headers=h)
    get("/api/admin/trends", headers=h)
    get("/api/admin/distributions", headers=h)
    get("/api/admin/user-domains", headers=h)
    get("/api/analytics/admin/bias-transparency", headers=h)

    # Admin idea-specific (id=1, may not exist)
    get("/api/admin/ideas/1", headers=h, expect=[200, 404])
    get("/api/admin/ideas/1/bias-breakdown", headers=h, expect=[200, 404])
    get("/api/admin/ideas/1/generation-trace", headers=h, expect=[200, 404])


# ── 4. IDEA GENERATION ────────────────────────────────────────────────────

def test_idea_generation():
    print(f"\n{Colors.BOLD}═══ IDEA GENERATION (user flow) ═══{Colors.END}")

    # Login as the test user
    token, _ = login("test@test.com", "TestUser@123")
    if not token:
        # Fallback: register a fresh user
        ts = int(time.time())
        email = f"gentest{ts}@test.com"
        try:
            r = requests.post(f"{BASE}/api/register", json={
                "email": email,
                "username": f"gentest{ts}",
                "password": "TestPass123",
                "skill_level": "intermediate"
            }, timeout=TIMEOUT)
        except Exception as e:
            print(f"  {Colors.FAIL}Registration timed out: {e}{Colors.END}")
            return None
        if r.status_code != 201:
            print(f"  {Colors.FAIL}Registration failed for generation test{Colors.END}")
            return None
        token = r.json().get("access_token")
    h = auth_header(token)

    # Get domains first
    dr = get("/api/domains", headers=h)
    if not dr:
        return
    domains = dr.json().get("domains", [])
    if not domains:
        print(f"  {Colors.WARN}No domains available — cannot test generation{Colors.END}")
        return

    domain_id = domains[0]["id"]
    domain_name = domains[0]["name"]
    print(f"  Using domain: {domain_name} (id={domain_id})")

    # Submit generation job (may take time for LLM — use longer timeout)
    gen_payload = {
        "subject": "AI-powered real-time code review tool for pull requests",
        "domain_id": domain_id
    }
    try:
        r = requests.post(f"{BASE}/api/ideas/generate", json=gen_payload, headers=h, timeout=180)
        report("POST /api/ideas/generate", r.status_code, [200, 201, 202])
    except Exception as e:
        report("POST /api/ideas/generate", 0, [200, 201, 202], str(e))
        r = None
    if not r or r.status_code not in (200, 201, 202):
        print(f"  {Colors.FAIL}Generation submission failed{Colors.END}")
        return

    resp = r.json()
    job_id = resp.get("job_id")
    idea = resp.get("idea")

    if job_id:
        print(f"  Job submitted: {job_id}")
        # Poll for completion (up to ~5 min for CPU-based LLM inference)
        for attempt in range(100):
            time.sleep(5)
            pr = get(f"/api/ideas/generate/{job_id}", headers=h, expect=[200, 202])
            if not pr:
                break
            pdata = pr.json()
            status = pdata.get("status", "")
            progress = pdata.get("progress", 0)
            print(f"  Poll {attempt+1}: status={status} progress={progress}")
            if status == "completed":
                idea = pdata.get("idea") or pdata.get("result", {}).get("idea")
                break
            elif status in ("failed", "error"):
                print(f"  {Colors.FAIL}Generation failed: {pdata.get('error', 'unknown')}{Colors.END}")
                break
        else:
            print(f"  {Colors.WARN}Generation timed out after 500s{Colors.END}")

    if idea:
        idea_id = idea.get("id")
        title = idea.get("title", "")[:60]
        novelty = idea.get("novelty_score") or idea.get("novelty_score_cached")
        quality = idea.get("quality_score") or idea.get("quality_score_cached")
        print(f"  {Colors.OK}✓ Idea generated: id={idea_id} title=\"{title}\" novelty={novelty} quality={quality}{Colors.END}")

        # Test idea detail
        if idea_id:
            get(f"/api/ideas/{idea_id}", headers=h)
            get(f"/api/ideas/{idea_id}/reviews", headers=h)
            get(f"/api/ideas/{idea_id}/feedbacks", headers=h)
            get(f"/api/ideas/{idea_id}/novelty-explanation", headers=h, expect=[200, 404])

            # Test feedback
            post(f"/api/ideas/{idea_id}/feedback", {"feedback_type": "upvote"}, headers=h, expect=[200, 201])

            # Test review
            post(f"/api/ideas/{idea_id}/review", {"rating": 4, "comment": "Smoke test review"}, headers=h, expect=[200, 201])

        return idea_id
    else:
        print(f"  {Colors.WARN}No idea object returned{Colors.END}")
        return None


# ── 5. NOVELTY CHECKING ──────────────────────────────────────────────────

def test_novelty_checking():
    print(f"\n{Colors.BOLD}═══ NOVELTY CHECKING ═══{Colors.END}")

    # Login with known user credentials
    token, _ = login("test@test.com", "TestUser@123")
    if not token:
        # Fallback: register a fresh user
        ts = int(time.time())
        email = f"novtest{ts}@test.com"
        try:
            r = requests.post(f"{BASE}/api/register", json={
                "email": email,
                "username": f"novtest{ts}",
                "password": "TestPass123",
                "skill_level": "advanced"
            }, timeout=TIMEOUT)
        except Exception as e:
            print(f"  {Colors.FAIL}Registration timed out: {e}{Colors.END}")
            return
        if r.status_code != 201:
            print(f"  {Colors.FAIL}Registration failed for novelty test{Colors.END}")
            return
        token = r.json().get("access_token")
    h = auth_header(token)

    # Get a domain
    try:
        dr = requests.get(f"{BASE}/api/domains", headers=h, timeout=TIMEOUT)
    except Exception as e:
        print(f"  {Colors.FAIL}Domains fetch timed out: {e}{Colors.END}")
        return
    domains = dr.json().get("domains", [])
    if not domains:
        print(f"  {Colors.WARN}No domains — skipping{Colors.END}")
        return
    domain_name = domains[0]["name"]

    # Test /api/novelty/analyze (LLM-based, can be slow)
    novelty_payload = {
        "description": "A blockchain-based decentralized identity verification system using zero-knowledge proofs for privacy-preserving KYC compliance in financial services",
        "domain": domain_name
    }
    old_timeout = TIMEOUT
    # Increase timeout for LLM-heavy novelty route
    r = None
    try:
        r = requests.post(f"{BASE}/api/novelty/analyze", json=novelty_payload, headers=h, timeout=120)
        report("POST /api/novelty/analyze", r.status_code, [200, 201])
    except Exception as e:
        report("POST /api/novelty/analyze", 0, [200, 201], str(e))
    if r and r.status_code in (200, 201):
        data = r.json()
        score = data.get("novelty_score", data.get("score", "N/A"))
        level = data.get("novelty_level", data.get("level", "N/A"))
        confidence = data.get("confidence", "N/A")
        engine = data.get("engine", "N/A")
        print(f"  {Colors.OK}✓ Novelty result: score={score} level={level} confidence={confidence} engine={engine}{Colors.END}")
    elif r:
        print(f"  Response: {r.text[:200]}")

    # Test /api/check_novelty (platform endpoint)
    r2 = post("/api/check_novelty", novelty_payload, headers=h, expect=[200, 201])
    if r2 and r2.status_code in (200, 201):
        data = r2.json()
        score = data.get("novelty_score", data.get("score", "N/A"))
        print(f"  {Colors.OK}✓ check_novelty result: score={score}{Colors.END}")

    # Test retrieval endpoint (requires domain_id, not domain name)
    # Get domain_id from domains list
    dr2 = requests.get(f"{BASE}/api/domains", headers=h, timeout=TIMEOUT)
    doms = dr2.json().get("domains", [])
    ret_domain_id = doms[0]["id"] if doms else None
    retrieval_payload = {
        "query": "decentralized identity blockchain zero knowledge proofs",
        "domain_id": ret_domain_id
    }
    r3 = post("/api/retrieval/sources", retrieval_payload, headers=h, expect=[200, 201])
    if r3 and r3.status_code in (200, 201):
        data = r3.json()
        sources = data.get("sources", [])
        print(f"  {Colors.OK}✓ Retrieval returned {len(sources)} sources{Colors.END}")


# ── 6. FRONTEND ROUTES ───────────────────────────────────────────────────

def test_frontend_routes():
    print(f"\n{Colors.BOLD}═══ FRONTEND ROUTES ═══{Colors.END}")
    frontend = "http://localhost:3000"

    routes = [
        "/",
        "/explore",
        "/login",
        "/register",
        "/user/dashboard",
        "/user/generate",
        "/user/novelty",
        "/user/my-ideas",
        "/admin",
        "/admin/review",
        "/admin/analytics",
        "/admin/abuse",
        "/idea/1",
        "/nonexistent-page",
    ]

    for route in routes:
        try:
            r = requests.get(f"{frontend}{route}", timeout=10)
            # Vite SPA always returns 200 with index.html
            ok = r.status_code == 200 and len(r.text) > 100
            tag = f"{Colors.OK}PASS{Colors.END}" if ok else f"{Colors.FAIL}FAIL{Colors.END}"
            global pass_count, fail_count
            if ok:
                pass_count += 1
            else:
                fail_count += 1
            print(f"  [{tag}] Frontend {route:30s}  => {r.status_code} ({len(r.text)} bytes)")
        except Exception as e:
            fail_count += 1
            print(f"  [{Colors.FAIL}FAIL{Colors.END}] Frontend {route:30s}  => ERROR: {e}")


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{Colors.BOLD}╔══════════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BOLD}║  InnovateSphere Full Route & Feature Test       ║{Colors.END}")
    print(f"{Colors.BOLD}╚══════════════════════════════════════════════════╝{Colors.END}")

    test_public_routes()
    test_user_routes()
    test_admin_routes()
    generated_idea_id = test_idea_generation()
    test_novelty_checking()
    test_frontend_routes()

    # Summary
    total = pass_count + fail_count
    print(f"\n{Colors.BOLD}{'═' * 55}{Colors.END}")
    print(f"  {Colors.OK}PASSED: {pass_count}{Colors.END}  |  {Colors.FAIL}FAILED: {fail_count}{Colors.END}  |  {Colors.WARN}WARNINGS: {warn_count}{Colors.END}  |  TOTAL: {total}")

    if failures:
        print(f"\n{Colors.FAIL}Failed tests:{Colors.END}")
        for label, got, expected, extra in failures:
            print(f"  • {label}: got {got}, expected {expected}")
            if extra:
                print(f"    {extra[:200]}")

    print(f"{Colors.BOLD}{'═' * 55}{Colors.END}")
    sys.exit(1 if fail_count > 0 else 0)
