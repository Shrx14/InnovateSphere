"""Live test of all major InnovateSphere features."""
import requests, json, time

BASE = 'http://localhost:5000/api'

# 1. Login
print('=== LOGIN ===')
r = requests.post(f'{BASE}/login', json={'email': 'test@example.com', 'password': 'AdminPass123'})
if r.status_code != 200:
    print(f'Login failed ({r.status_code}), trying register...')
    r = requests.post(f'{BASE}/register', json={'email': 'testuser@test.com', 'password': 'Test1234!', 'username': 'testuser'})
    print(f'Register: {r.status_code}')
    if r.status_code in (200, 201):
        tokens = r.json()
    else:
        print(r.json())
        exit(1)
else:
    tokens = r.json()

at = tokens.get('access_token')
print(f'Login OK - got access_token: {bool(at)}')
headers = {'Authorization': f'Bearer {at}'}

# 2. Get domains
print('\n=== DOMAINS ===')
r = requests.get(f'{BASE}/domains', headers=headers)
print(f'Domains: {r.status_code} - {len(r.json().get("domains", []))} domains')
domains = r.json().get('domains', [])
domain_id = domains[0]['id'] if domains else 1
domain_name = domains[0]['name'] if domains else 'AI & ML'
print(f'Using domain: {domain_name} (id={domain_id})')

# 3. Test Novelty Analysis (synchronous)
print('\n=== NOVELTY ANALYSIS ===')
r = requests.post(f'{BASE}/novelty/analyze', headers=headers, json={
    'description': 'A federated learning system for privacy-preserving medical image analysis across hospital networks',
    'domain': domain_name
})
print(f'Novelty: {r.status_code}')
if r.status_code == 200:
    nov = r.json()
    print(f'  Score: {nov.get("novelty_score")}')
    print(f'  Level: {nov.get("novelty_level")}')
    print(f'  Confidence: {nov.get("confidence")}')
    print(f'  Sources: {len(nov.get("sources", []))}')
    ik = list(nov.get("insights", {}).keys())
    print(f'  Insights keys: {ik[:5]}')
else:
    print(f'  Error: {r.text[:300]}')

# 4. Test Idea Generation (async with polling)
print('\n=== IDEA GENERATION ===')
r = requests.post(f'{BASE}/ideas/generate', headers=headers, json={
    'query': 'Build an AI-powered code review assistant that detects security vulnerabilities using static analysis and LLM reasoning',
    'domain_id': domain_id
})
print(f'Generate start: {r.status_code}')
if r.status_code == 202:
    job_id = r.json()['job_id']
    print(f'  Job ID: {job_id}')
    
    for i in range(60):
        time.sleep(3)
        r = requests.get(f'{BASE}/ideas/generate/{job_id}', headers=headers)
        data = r.json()
        status = data.get('status', 'unknown')
        phase = data.get('phase', '?')
        progress = data.get('progress', 0)
        print(f'  Poll {i+1}: status={status} phase={phase} progress={progress}%')
        
        if status == 'completed':
            result = data.get('result', {})
            print(f'  COMPLETED!')
            print(f'  Title: {result.get("title", "N/A")}')
            print(f'  Novelty: {result.get("novelty_score")}')
            print(f'  Quality: {result.get("quality_score")}')
            print(f'  Sources: {result.get("source_count", "?")}')
            print(f'  ID: {result.get("id")}')
            break
        elif status == 'failed':
            print(f'  FAILED: {data.get("error", "unknown")}')
            break
    else:
        print('  TIMEOUT after 60 polls')
elif r.status_code == 429:
    print(f'  Rate limited - try again later')
else:
    print(f'  Error: {r.text[:300]}')

# 5. Test public endpoints
print('\n=== PUBLIC ENDPOINTS ===')
r = requests.get(f'{BASE}/public/stats')
print(f'Public stats: {r.status_code} - {r.json()}')

r = requests.get(f'{BASE}/public/top-ideas')
top = r.json().get('ideas', [])
print(f'Top ideas: {r.status_code} - {len(top)} ideas')
if top:
    keys = list(top[0].keys())
    print(f'  Keys in first idea: {keys}')
    has_quality = 'quality_score' in keys
    print(f'  Quality score leaked? {has_quality}')

# 6. Test user's ideas
print('\n=== MY IDEAS ===')
r = requests.get(f'{BASE}/ideas/mine', headers=headers)
print(f'My ideas: {r.status_code} - {len(r.json().get("ideas", []))} ideas')

# 7. Test bookmarked
print('\n=== BOOKMARKED ===')
r = requests.get(f'{BASE}/ideas/bookmarked', headers=headers)
print(f'Bookmarked: {r.status_code} - {len(r.json().get("ideas", []))} bookmarked')

# 8. Test profile
print('\n=== PROFILE ===')
r = requests.get(f'{BASE}/user/profile', headers=headers)
print(f'Profile: {r.status_code}')
if r.status_code == 200:
    p = r.json()
    print(f'  Username: {p.get("username")}')
    print(f'  Email: {p.get("email")}')
    print(f'  Role: {p.get("role")}')

# 9. Test admin endpoints (if admin)
print('\n=== ADMIN ENDPOINTS ===')
r = requests.get(f'{BASE}/admin/ideas/quality-review', headers=headers)
print(f'Admin review queue: {r.status_code}')
if r.status_code == 200:
    ideas = r.json().get('ideas', [])
    print(f'  Ideas in queue: {len(ideas)}')

r = requests.get(f'{BASE}/analytics/admin/kpis', headers=headers)
print(f'Admin KPIs: {r.status_code}')
if r.status_code == 200:
    kpis = r.json()
    print(f'  Total ideas: {kpis.get("total_ideas")}')
    print(f'  Avg novelty: {kpis.get("avg_novelty")}')
    print(f'  Avg quality: {kpis.get("avg_quality")}')
    print(f'  Rejection rate: {kpis.get("rejection_rate")}')

r = requests.get(f'{BASE}/analytics/admin/bias-transparency', headers=headers)
print(f'Admin bias transparency: {r.status_code}')
if r.status_code == 200:
    bias = r.json()
    print(f'  Verdicts: {bias.get("admin_verdicts")}')
    print(f'  Penalty stats: {bias.get("penalty_impact_stats")}')

r = requests.get(f'{BASE}/ai/pipeline-version', headers=headers)
print(f'Pipeline version: {r.status_code} - {r.json()}')

print('\n=== ALL TESTS COMPLETE ===')
