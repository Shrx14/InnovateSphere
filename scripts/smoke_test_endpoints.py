#!/usr/bin/env python3
"""Quick endpoint smoke test for all major API routes."""
import requests
import json
import sys

BASE = "http://127.0.0.1:5000/api"

def test(label, method, url, headers=None, json_body=None, expect_status=200):
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        else:
            r = requests.post(url, headers=headers, json=json_body, timeout=15)
        ok = r.status_code == expect_status
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}: {r.status_code}", end="")
        return r
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        return None

def main():
    print("=" * 60)
    print("InnovateSphere API Smoke Test")
    print("=" * 60)

    # --- Public endpoints ---
    print("\n--- Public Endpoints ---")

    r = test("Health", "GET", f"{BASE}/health")
    if r: print(f" -> {r.json()}")

    r = test("Public stats", "GET", f"{BASE}/public/stats")
    if r: print(f" -> {r.json()}")

    r = test("Domains", "GET", f"{BASE}/domains")
    if r:
        domains = r.json().get("domains", [])
        print(f" -> {len(domains)} domains")

    r = test("Top domains", "GET", f"{BASE}/public/top-domains")
    if r:
        d = r.json().get("domains", [])
        print(f" -> {len(d)} domains, first: {d[0] if d else 'none'}")

    r = test("Top ideas", "GET", f"{BASE}/public/top-ideas")
    if r:
        ideas = r.json().get("ideas", [])
        print(f" -> {len(ideas)} ideas")
        if ideas:
            i = ideas[0]
            has_novelty = i.get("novelty_score") is not None
            has_quality = i.get("quality_score") is not None
            print(f"    First: novelty={i.get('novelty_score')} quality={i.get('quality_score')} has_scores={has_novelty and has_quality}")

    r = test("Public ideas", "GET", f"{BASE}/public/ideas?page=1&limit=3")
    if r:
        d = r.json()
        ideas = d.get("ideas", [])
        meta = d.get("meta", {})
        print(f" -> total={meta.get('total')} pages={meta.get('pages')}")
        if ideas:
            i = ideas[0]
            print(f"    First: novelty={i.get('novelty_score')} quality={i.get('quality_score')} has_problem={bool(i.get('problem_statement'))}")

    # Get a valid idea ID
    first_idea_id = None
    r2 = requests.get(f"{BASE}/public/ideas?limit=1", timeout=10)
    if r2.status_code == 200 and r2.json().get("ideas"):
        first_idea_id = r2.json()["ideas"][0]["id"]

    if first_idea_id:
        r = test("Public idea detail", "GET", f"{BASE}/public/ideas/{first_idea_id}")
        if r:
            idea = r.json().get("idea", {})
            sources = idea.get("sources", [])
            has_tier = sources[0].get("relevance_tier") if sources else None
            print(f" -> sources={len(sources)} relevance_tier={has_tier}")

    # --- Auth ---
    print("\n--- Authentication ---")
    r = test("Login (admin)", "POST", f"{BASE}/login",
             json_body={"email": "test@example.com", "password": "AdminPass123"})
    token = None
    if r:
        data = r.json()
        token = data.get("access_token")
        print(f" -> has_token={bool(token)}")

    if not token:
        print("\n!!! Cannot test authenticated endpoints without token !!!")
        print("Trying other users...")
        for email, pwd in [("admin1@example.com", "AdminPass123"), ("admin@example.com", "admin123")]:
            r = requests.post(f"{BASE}/login", json={"email": email, "password": pwd}, timeout=10)
            if r.status_code == 200:
                token = r.json().get("access_token")
                print(f"  Found working: {email}")
                break
    
    if not token:
        print("Cannot login. Skipping authenticated tests.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # --- Authenticated user endpoints ---
    print("\n--- Authenticated User Endpoints ---")

    r = test("My ideas", "GET", f"{BASE}/ideas/mine", headers=headers)
    if r:
        d = r.json()
        ideas = d.get("ideas", [])
        print(f" -> {len(ideas)} ideas, total={d.get('meta',{}).get('total')}")
        if ideas:
            i = ideas[0]
            print(f"    has_problem_stmt={bool(i.get('problem_statement'))} novelty={i.get('novelty_score')} status={i.get('status')}")

    if first_idea_id:
        r = test("Idea detail (auth)", "GET", f"{BASE}/ideas/{first_idea_id}", headers=headers)
        if r:
            idea = r.json().get("idea", {})
            print(f" -> novelty={idea.get('novelty_score')} quality={idea.get('quality_score')} status={idea.get('status')}")
            print(f"    sources={len(idea.get('sources',[]))} has_source_id={'id' in idea.get('sources',[{}])[0] if idea.get('sources') else False}")

        r = test("Novelty explanation", "GET", f"{BASE}/ideas/{first_idea_id}/novelty-explanation", headers=headers)
        if r:
            d = r.json()
            print(f" -> has_explanation={bool(d.get('explanation'))}")

        r = test("Idea reviews list", "GET", f"{BASE}/ideas/{first_idea_id}/reviews", headers=headers)
        if r:
            print(f" -> {len(r.json().get('reviews', []))} reviews")

        r = test("Idea feedbacks list", "GET", f"{BASE}/ideas/{first_idea_id}/feedbacks", headers=headers)
        if r:
            d = r.json()
            print(f" -> {len(d.get('feedbacks', []))} feedbacks, by_type={list(d.get('by_type', {}).keys())}")

    # --- Admin endpoints ---
    print("\n--- Admin Endpoints ---")

    r = test("Admin KPIs", "GET", f"{BASE}/analytics/admin/kpis", headers=headers)
    if r:
        k = r.json()
        print(f" -> total_ideas={k.get('total_ideas')} avg_novelty={k.get('avg_novelty')} avg_quality={k.get('avg_quality')}")
        print(f"    rejection_rate={k.get('rejection_rate')} avg_rating={k.get('avg_rating')} feedback_dist={k.get('feedback_distribution')}")

    r = test("Admin domains", "GET", f"{BASE}/admin/domains", headers=headers)
    if r:
        d = r.json().get("domains", [])
        print(f" -> {len(d)} domains")
        if d:
            print(f"    First: {d[0]}")

    r = test("Admin trends", "GET", f"{BASE}/admin/trends", headers=headers)
    if r:
        t = r.json().get("trends", [])
        print(f" -> {len(t)} data points")
        if t:
            print(f"    Range: {t[0].get('date')} to {t[-1].get('date')}")

    r = test("Admin distributions", "GET", f"{BASE}/admin/distributions", headers=headers)
    if r:
        d = r.json()
        print(f" -> novelty_buckets={len(d.get('novelty',[]))} quality_buckets={len(d.get('quality',[]))}")
        if d.get("novelty"):
            print(f"    Novelty: {d['novelty'][:3]}...")
        if d.get("quality"):
            print(f"    Quality: {d['quality'][:3]}...")

    r = test("Admin user-domains", "GET", f"{BASE}/admin/user-domains", headers=headers)
    if r:
        d = r.json().get("user_domains", [])
        print(f" -> {len(d)} domains with users")

    r = test("Admin review queue", "GET", f"{BASE}/admin/ideas/quality-review", headers=headers)
    if r:
        d = r.json()
        print(f" -> {d.get('meta',{}).get('total')} ideas in queue")

    r = test("Abuse events", "GET", f"{BASE}/admin/abuse-events?per_page=5", headers=headers)
    if r:
        d = r.json()
        print(f" -> {len(d.get('events',[]))} events shown, total={d.get('meta',{}).get('total')}")

    r = test("Bias transparency", "GET", f"{BASE}/analytics/admin/bias-transparency", headers=headers)
    if r:
        d = r.json()
        print(f" -> keys={list(d.keys())}")

    if first_idea_id:
        r = test("Admin idea detail", "GET", f"{BASE}/admin/ideas/{first_idea_id}", headers=headers)
        if r:
            d = r.json()
            print(f" -> sources={len(d.get('sources',[]))} reviews={len(d.get('reviews',[]))} feedbacks={len(d.get('feedback_history',[]))}")

        r = test("Generation trace", "GET", f"{BASE}/admin/ideas/{first_idea_id}/generation-trace", headers=headers)
        if r:
            gt = r.json().get("generation_trace", {})
            phases = [k for k in gt.keys() if k.startswith("phase_")]
            print(f" -> phases={phases} pipeline={gt.get('ai_pipeline_version')}")

        r = test("Bias breakdown", "GET", f"{BASE}/admin/ideas/{first_idea_id}/bias-breakdown", headers=headers)
        if r:
            print(f" -> novelty={r.json().get('novelty_score')} constraints={list(r.json().get('constraints',{}).keys())}")

    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
