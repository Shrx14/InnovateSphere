"""
Novelty Scoring Test Suite
Tests the novelty analysis and scoring system
Usage: python scripts/test_novelty_scoring.py
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
    ORANGE = '\033[33m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_test(name, status, details=""):
    """Print test result with color"""
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    print(f"{icon} {name}")
    if details:
        print(f"  {Colors.BLUE}→{Colors.RESET} {details}")

def print_section(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'='*70}{Colors.RESET}")

def print_score_breakdown(score_data):
    """Pretty print novelty score breakdown"""
    if not score_data:
        return
    
    print(f"\n  {Colors.ORANGE}Score Breakdown:{Colors.RESET}")
    
    # Overall score
    if "novelty_score" in score_data:
        score = score_data["novelty_score"]
        print(f"    Overall Novelty: {Colors.BOLD}{score}{Colors.RESET}/10")
    
    # Confidence
    if "confidence_score" in score_data:
        conf = score_data["confidence_score"]
        bar_length = int(conf * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"    Confidence: [{bar}] {conf:.1%}")
    
    # Signals
    if "signals" in score_data:
        signals = score_data["signals"]
        print(f"    {Colors.BOLD}Key Signals:{Colors.RESET}")
        for signal_name, value in list(signals.items())[:5]:
            value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
            print(f"      • {signal_name}: {value_str}")

def login(email, password):
    """Test login endpoint"""
    print_section("STEP 1: USER LOGIN")
    
    url = f"{BASE}/api/login"
    try:
        resp = requests.post(
            url,
            json={"email": email, "password": password},
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            user_id = data.get("user_id", "N/A")
            print_test("Login successful", True, f"User ID: {user_id}, Token: {token[:20]}...")
            return token
        else:
            print_test("Login", False, f"Status {resp.status_code}")
            print(f"  Response: {resp.text[:100]}")
            return None
    except Exception as e:
        print_test("Login", False, str(e))
        return None

def generate_idea(token, query, domain_id=1):
    """Generate an idea and return it with scoring"""
    print_section("STEP 2: GENERATE IDEA WITH NOVELTY SCORING")
    
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
        
        print(f"  Response Status: {resp.status_code}")
        
        if resp.status_code == 201:
            data = resp.json()
            idea_id = data.get("id")
            title = data.get("title", "N/A")
            novelty_score = data.get("novelty_score", "N/A")
            quality_score = data.get("quality_score", "N/A")
            
            print_test("Idea Generated", True, f"ID: {idea_id}")
            print_test("Novelty Score Present", True, f"Score: {novelty_score}/10")
            print_test("Quality Score Present", True, f"Score: {quality_score}")
            
            # Show full response
            print(f"\n  {Colors.ORANGE}Generated Idea:{Colors.RESET}")
            print(f"    Title: {title}")
            print(f"    Problem: {data.get('problem_statement', 'N/A')[:80]}...")
            print_score_breakdown(data)
            
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

def test_novelty_explanation(token, idea_id):
    """Test novelty explanation endpoint to get detailed scoring breakdown"""
    print_section("STEP 3: NOVELTY SCORING ANALYSIS")
    
    url = f"{BASE}/api/ideas/{idea_id}/novelty-explanation"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"  Fetching detailed novelty analysis for idea {idea_id}...")
        
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"  Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Main scoring info
            print_test("Novelty Explanation Retrieved", True)
            
            # Extract and display components
            novelty_score = data.get("novelty_score", "N/A")
            confidence = data.get("confidence_score", "N/A")
            explanation = data.get("explanation", "")
            signals = data.get("signals", {})
            penalties = data.get("penalties", {})
            
            print(f"\n  {Colors.ORANGE}Novelty Scoring Breakdown:{Colors.RESET}")
            print(f"    Score: {Colors.BOLD}{novelty_score}{Colors.RESET}/10")
            print(f"    Confidence: {Colors.BOLD}{confidence:.1%}{Colors.RESET}")
            print(f"    Explanation: {explanation[:120]}...")
            
            if signals:
                print(f"\n  {Colors.ORANGE}Positive Signals:{Colors.RESET}")
                pos_signals = {k: v for k, v in signals.items() if v > 0}
                for sig, val in list(pos_signals.items())[:5]:
                    pct = (val / sum(v for v in signals.values())*100) if sum(v for v in signals.values()) > 0 else 0
                    print(f"    • {sig}: +{val:.2f} ({pct:.1f}%)")
            
            if penalties:
                print(f"\n  {Colors.ORANGE}Applied Penalties:{Colors.RESET}")
                for pen, val in list(penalties.items())[:3]:
                    print(f"    • {pen}: -{val:.2f}")
            
            return True, data
        else:
            print(f"  Response: {resp.text[:200]}")
            print_test("Novelty Explanation", False, f"Status {resp.status_code}")
            return False, None
            
    except Exception as e:
        print_test("Novelty Explanation", False, str(e))
        return False, None

def test_multiple_queries(token):
    """Test novelty scoring on different query types"""
    print_section("STEP 4: COMPARE NOVELTY SCORES - DIFFERENT QUERIES")
    
    test_queries = [
        ("AI-powered chatbot for customer service", 1),
        ("Quantum computing application for drug discovery", 1),
        ("Blockchain-based identity verification system", 2),
        ("IoT smart home automation platform", 3),
    ]
    
    results = []
    
    for i, (query, domain_id) in enumerate(test_queries, 1):
        try:
            print(f"\n  Test {i}: {query[:50]}...")
            
            url = f"{BASE}/api/ideas/generate"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {"subject": query, "domain_id": domain_id}
            
            resp = requests.post(url, json=payload, headers=headers, timeout=300)
            
            if resp.status_code == 201:
                data = resp.json()
                score = data.get("novelty_score", 0)
                quality = data.get("quality_score", 0)
                results.append({
                    "query": query[:40],
                    "score": score,
                    "quality": quality,
                    "id": data.get("id")
                })
                print(f"    ✓ Novelty: {score}/10, Quality: {quality}")
            else:
                print(f"    ✗ Failed with status {resp.status_code}")
                
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")
    
    # Summary table
    print(f"\n  {Colors.ORANGE}Score Comparison:{Colors.RESET}")
    print(f"    {'Query':<43} {'Novelty':<10} {'Quality':<10}")
    print(f"    {'-'*63}")
    for r in results:
        print(f"    {r['query']:<43} {r['score']:<10.1f} {r['quality']:<10.1f}")
    
    return results

def test_public_ideas_scores():
    """Check novelty scores in public ideas without authentication"""
    print_section("STEP 5: PUBLIC IDEAS - NOVELTY SCORE VISIBILITY")
    
    url = f"{BASE}/api/public/ideas"
    
    try:
        print(f"  Fetching public ideas (no authentication)...")
        
        resp = requests.get(url, params={"limit": 10}, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            ideas = data.get("ideas", [])
            
            print_test("Public Ideas Retrieved", True, f"Found {len(ideas)} ideas")
            
            if ideas:
                print(f"\n  {Colors.ORANGE}Public Ideas Novelty Scores:{Colors.RESET}")
                print(f"    {'Title':<45} {'Novelty':<10} {'Quality':<10}")
                print(f"    {'-'*65}")
                
                for idea in ideas[:5]:
                    title = idea.get("title", "N/A")[:40]
                    novelty = idea.get("novelty_score", "N/A")
                    quality = idea.get("quality_score", "N/A")
                    
                    novelty_str = f"{novelty:.1f}" if isinstance(novelty, (int, float)) else "—"
                    quality_str = f"{quality:.1f}" if isinstance(quality, (int, float)) else "—"
                    
                    print(f"    {title:<45} {novelty_str:<10} {quality_str:<10}")
            
            return True
        else:
            print_test("Public Ideas", False, f"Status {resp.status_code}")
            return False
            
    except Exception as e:
        print_test("Public Ideas", False, str(e))
        return False

def main():
    """Run all novelty scoring tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}InnovateSphere Novelty Scoring Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    
    # Check server
    try:
        resp = requests.get(f"{BASE}/api/public/ideas", timeout=5)
        print_test("Backend Server", True, f"Running on {BASE}")
    except:
        print_test("Backend Server", False, f"Not reachable at {BASE}")
        print(f"\n{Colors.RED}Please start backend:{{Colors.RESET}}")
        print(f"  python -m backend.run")
        sys.exit(1)
    
    # Credentials
    email = "test@test.com"
    password = "TestUser@123"
    
    # Login
    token = login(email, password)
    if not token:
        print(f"\n{Colors.RED}Cannot proceed without authentication{Colors.RESET}")
        sys.exit(1)
    
    # Generate idea and get novelty score
    query = "Smart Attendance System using facial recognition with liveness detection"
    idea_id, idea_data = generate_idea(token, query, domain_id=1)
    
    # Get detailed novelty analysis if idea generated
    if idea_id:
        test_novelty_explanation(token, idea_id)
    
    # Compare multiple queries
    print()
    test_multiple_queries(token)
    
    # Check public ideas
    print()
    test_public_ideas_scores()
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"{Colors.GREEN}✓ Novelty Scoring Tests Completed{Colors.RESET}")
    print(f"{Colors.BLUE}Check results above for score calculations and breakdowns{Colors.RESET}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()
