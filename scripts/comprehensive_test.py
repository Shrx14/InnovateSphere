"""
Comprehensive test suite: 
1. Login + Idea Generation + Novelty Analysis
2. Public Ideas Search (no login required)
"""
import sys
import json
import requests
from datetime import datetime

BASE = "http://127.0.0.1:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, status, details=""):
    """Print test result with color"""
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    print(f"{icon} {name}")
    if details:
        print(f"  {Colors.BLUE}→{Colors.RESET} {details}")

def print_section(title):
    """Print section header"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}")

def login(email, password):
    """Test login endpoint"""
    print_section("TEST 1: USER LOGIN")
    
    url = f"{BASE}/api/login"
    try:
        resp = requests.post(
            url, 
            json={"email": email, "password": password}, 
            timeout=30
        )
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            print_test("Login", True, f"Token received: {token[:20]}...")
            return token
        else:
            print(f"  Response: {resp.text}")
            print_test("Login", False, f"Status {resp.status_code}")
            return None
    except Exception as e:
        print_test("Login", False, str(e))
        return None

def generate_idea(token, query, domain_id):
    """Test idea generation endpoint"""
    print_section("TEST 2: IDEA GENERATION")
    
    url = f"{BASE}/api/ideas/generate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "subject": query,
        "domain_id": domain_id
    }
    
    try:
        print(f"  Query: {query}")
        print(f"  Domain ID: {domain_id}")
        print(f"  Timeout: 300s (waiting for model execution...)")
        
        resp = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            timeout=300
        )
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 201:
            data = resp.json()
            idea_id = data.get("id")
            title = data.get("title", "N/A")
            novelty_score = data.get("novelty_score", "N/A")
            print_test("Idea Generation", True, f"ID: {idea_id}, Title: {title}, Novelty: {novelty_score}")
            return idea_id, data
        else:
            print(f"  Response: {resp.text[:200]}")
            print_test("Idea Generation", False, f"Status {resp.status_code}")
            return None, None
    except requests.Timeout:
        print_test("Idea Generation", False, "Request timeout (model execution taking too long)")
        return None, None
    except Exception as e:
        print_test("Idea Generation", False, str(e))
        return None, None

def get_novelty_analysis(token, idea_id):
    """Test novelty explanation endpoint"""
    print_section("TEST 3: NOVELTY ANALYSIS")
    
    url = f"{BASE}/api/ideas/{idea_id}/novelty-explanation"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"  Idea ID: {idea_id}")
        
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            signals = data.get("signals", {})
            confidence = data.get("confidence_score", "N/A")
            explanation = data.get("explanation", "N/A")
            
            print_test("Novelty Explanation Retrieved", True, f"Confidence: {confidence}")
            print(f"  Explanation: {explanation[:100]}...")
            
            if signals:
                print(f"  Key Signals:")
                for signal_name, value in list(signals.items())[:3]:
                    print(f"    - {signal_name}: {value}")
            
            return True, data
        else:
            print(f"  Response: {resp.text[:200]}")
            print_test("Novelty Explanation Retrieved", False, f"Status {resp.status_code}")
            return False, None
    except Exception as e:
        print_test("Novelty Explanation Retrieved", False, str(e))
        return False, None

def search_public_ideas(query=None, domain=None):
    """Test public ideas search (no authentication required)"""
    print_section("TEST 4: PUBLIC IDEAS SEARCH (NO LOGIN)")
    
    url = f"{BASE}/api/public/ideas"
    params = {}
    
    if query:
        params["q"] = query
    if domain:
        params["domain"] = domain
    
    params["page"] = 1
    params["limit"] = 5
    
    try:
        print(f"  Query: {query if query else 'None (browse all)'}")
        print(f"  Domain: {domain if domain else 'Any'}")
        print(f"  No authentication required")
        
        resp = requests.get(url, params=params, timeout=30)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            ideas = data.get("ideas", [])
            total = data.get("meta", {}).get("total", 0)
            pages = data.get("meta", {}).get("pages", 0)
            
            print_test("Public Ideas Retrieved", True, f"Found {total} ideas, {len(ideas)} on page 1")
            
            if ideas:
                print(f"  First 3 ideas:")
                for i, idea in enumerate(ideas[:3], 1):
                    print(f"    {i}. {idea.get('title', 'N/A')}")
                    print(f"       Novelty: {idea.get('novelty_score', 'N/A')}")
            
            return True, data
        else:
            print(f"  Response: {resp.text[:200]}")
            print_test("Public Ideas Retrieved", False, f"Status {resp.status_code}")
            return False, None
    except Exception as e:
        print_test("Public Ideas Retrieved", False, str(e))
        return False, None

def search_by_domain(domain_name):
    """Test searching public ideas by domain"""
    print_section("TEST 5: DOMAIN-SPECIFIC PUBLIC SEARCH")
    
    return search_public_ideas(domain=domain_name)

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}InnovateSphere Comprehensive Testing Suite{Colors.RESET}")
    print(f"{Colors.BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    # Check if server is running
    try:
        resp = requests.get(f"{BASE}/api/public/ideas", timeout=5)
        print_test("Server Connection", True, "Backend is running")
    except Exception as e:
        print_test("Server Connection", False, f"Cannot reach backend at {BASE}")
        print(f"\n{Colors.RED}Please start the backend server first:{Colors.RESET}")
        print(f"  cd backend && python -m backend.run")
        sys.exit(1)
    
    # Credentials
    email = "test@test.com"
    password = "TestUser@123"
    
    # Test authenticated flow
    token = login(email, password)
    if not token:
        print(f"\n{Colors.RED}Cannot proceed without authentication{Colors.RESET}")
        sys.exit(1)
    
    # Generate idea
    query = "Smart Attendance using facial recognition with advanced anti-spoofing"
    idea_id, idea_data = generate_idea(token, query, domain_id=1)
    
    # Get novelty analysis if idea was generated
    if idea_id:
        get_novelty_analysis(token, idea_id)
    
    # Test public search
    search_public_ideas()
    search_public_ideas(query="AI", domain="Artificial Intelligence")
    search_by_domain("Artificial Intelligence")
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"{Colors.GREEN}All core tests executed{Colors.RESET}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()
