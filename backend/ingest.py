"""Ingestion script: fetch ArXiv entries, embed with sentence-transformers,
and store projects + embeddings in the database.
"""
import os

# Ensure arXiv package uses HTTPS endpoint to avoid HTTP 301 redirects
os.environ["ARXIV_API_URL"] = "https://export.arxiv.org/api/query"

from sentence_transformers import SentenceTransformer
import arxiv

from app import app, db
from models import Project, ProjectVector
from sqlalchemy.exc import IntegrityError

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
MAX_RESULTS = int(os.getenv('INGEST_MAX', '30'))


def fetch_arxiv_papers(query, max_results=MAX_RESULTS):
    """Fetch papers from arXiv using HTTPS and parse the Atom feed with feedparser.
    This avoids relying on the `arxiv` package's default HTTP behavior which caused
    redirects (301)."""
    import requests
    import feedparser
    print(f"Fetching ArXiv via HTTPS: {query} (max {max_results})")
    base = 'https://export.arxiv.org/api/query'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }
    resp = requests.get(base, params=params, timeout=30)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    papers = []
    for entry in feed.entries:
        papers.append({
            'source': 'arxiv',
            'title': entry.get('title', '').strip(),
            'description': entry.get('summary', '').replace('\n', ' '),
            'url': entry.get('id', '') or entry.get('link', '')
        })
    return papers


def embed_and_store(items, model):
    print(f"Embedding and storing {len(items)} items...")
    added = 0
    skipped = 0
    with app.app_context():
        for it in items:
            # skip duplicates by URL
            exists = Project.query.filter_by(url=it['url']).first()
            if exists:
                skipped += 1
                continue

            p = Project(source=it['source'], title=it['title'], description=it['description'], url=it['url'])
            db.session.add(p)
            db.session.flush()

            text = f"Title: {it['title']}. Description: {it['description'] or ''}"
            embedding = model.encode(text)

            pv = ProjectVector(project_id=p.id, embedding=embedding.tolist())
            db.session.add(pv)
            try:
                db.session.commit()
                added += 1
            except IntegrityError:
                db.session.rollback()
                skipped += 1
            except Exception as e:
                db.session.rollback()
                print('Error saving:', e)
                skipped += 1

    print(f"Done. Added: {added}, Skipped: {skipped}")


def main():
    print('Loading embedding model...')
    model = SentenceTransformer(EMBEDDING_MODEL)
    print('Model loaded.')

    # Ensure tables for Project/ProjectVector exist (models may have been added after app startup)
    with app.app_context():
        db.create_all()

    queries = [ '"machine learning" AND project', '"web development" AND project', 'blockchain AND project', 'react AND project' ]
    all_items = []
    for q in queries:
        all_items.extend(fetch_arxiv_papers(q, max_results=MAX_RESULTS))

    if not all_items:
        print('No items fetched.')
        return

    embed_and_store(all_items, model)


if __name__ == '__main__':
    main()
import os
os.environ["ARXIV_API_URL"] = "https://export.arxiv.org/api/query"
from sentence_transformers import SentenceTransformer
import arxiv

from app import app, db
from models import Project, ProjectVector
from sqlalchemy.exc import IntegrityError

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
MAX_RESULTS = int(os.getenv('INGEST_MAX', '30'))


def fetch_arxiv_papers(query, max_results=MAX_RESULTS):
    """Fetch arXiv results directly over HTTPS using requests + feedparser.
    This avoids potential HTTP->HTTPS redirects that some environments reject.
    """
    import requests
    import feedparser
    from urllib.parse import quote_plus

    print(f"Fetching ArXiv (HTTPS): {query} (max {max_results})")
    base = 'https://export.arxiv.org/api/query'
    params = f"search_query={quote_plus(query)}&start=0&max_results={max_results}&sortBy=submittedDate"
    url = f"{base}?{params}"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching arXiv feed: {e}")
        return []

    feed = feedparser.parse(resp.text)
    papers = []
    for entry in feed.entries:
        # Choose a stable URL: prefer pdf link if available, else entry.id
        pdf_url = None
        if 'links' in entry:
            for l in entry.links:
                if l.get('type') == 'application/pdf' or l.get('title', '').lower() == 'pdf':
                    pdf_url = l.get('href')
                    break

        papers.append({
            'source': 'arxiv',
            'title': entry.get('title', '').strip(),
            'description': entry.get('summary', '').replace('\n', ' ').strip(),
            'url': pdf_url or entry.get('id') or entry.get('link')
        })

    return papers


def embed_and_store(items, model):
    print(f"Embedding and storing {len(items)} items...")
    added = 0
    skipped = 0
    with app.app_context():
        for it in items:
            # skip duplicates by URL
            exists = Project.query.filter_by(url=it['url']).first()
            if exists:
                skipped += 1
                continue

            p = Project(source=it['source'], title=it['title'], description=it['description'], url=it['url'])
            db.session.add(p)
            db.session.flush()

            text = f"Title: {it['title']}. Description: {it['description'] or ''}"
            embedding = model.encode(text)

            pv = ProjectVector(project_id=p.id, embedding=embedding.tolist())
            db.session.add(pv)
            try:
                db.session.commit()
                added += 1
            except IntegrityError:
                db.session.rollback()
                skipped += 1
            except Exception as e:
                db.session.rollback()
                print('Error saving:', e)
                skipped += 1

    print(f"Done. Added: {added}, Skipped: {skipped}")


def main():
    print('Loading embedding model...')
    model = SentenceTransformer(EMBEDDING_MODEL)
    print('Model loaded.')

    queries = [ '"machine learning" AND project', '"web development" AND project', 'blockchain AND project', 'react AND project' ]
    all_items = []
    for q in queries:
        all_items.extend(fetch_arxiv_papers(q, max_results=MAX_RESULTS))

    if not all_items:
        print('No items fetched.')
        return

    embed_and_store(all_items, model)


if __name__ == '__main__':
    main()
