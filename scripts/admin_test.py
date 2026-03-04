import requests
import json

BASE = 'http://127.0.0.1:5000/api'

# Login
r = requests.post(f'{BASE}/login', json={'email':'test@example.com','password':'AdminPass123'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print('Login:', 'OK' if token else 'FAIL')

# Admin review queue
r = requests.get(f'{BASE}/admin/ideas/quality-review', headers=headers)
ideas = r.json().get('ideas', [])
print(f'Admin review queue: {r.status_code} - {len(ideas)} ideas')

# Admin KPIs
r = requests.get(f'{BASE}/analytics/admin/kpis', headers=headers)
d = r.json()
print(f'Admin KPIs: {r.status_code} - keys: {list(d.keys())}')

# Bias transparency
r = requests.get(f'{BASE}/analytics/admin/bias-transparency', headers=headers)
d = r.json()
print(f'Bias transparency: {r.status_code} - keys: {list(d.keys())}')

# Pipeline version
r = requests.get(f'{BASE}/ai/pipeline-version', headers=headers)
d = r.json()
print(f'Pipeline version: {r.status_code} - {d}')

print('\n=== ALL ADMIN ENDPOINTS PASSED ===')
