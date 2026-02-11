from backend.app import app

print('Registered routes:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f"{rule.rule} -> {rule.endpoint}")

with app.test_client() as c:
    r = c.post('/api/check_novelty', json={})
    print('\nPOST /api/check_novelty status:', r.status_code)
    print('Body:')
    print(r.get_data(as_text=True))
