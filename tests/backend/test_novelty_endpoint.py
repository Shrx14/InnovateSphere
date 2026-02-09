import sys
import os
import types
import pytest
# Ensure repo root is on sys.path so `import app` works when pytest runs from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.app import app

class DummyModel:
    def encode(self, text):
        # return a fixed-size embedding (384 dims)
        return [0.0] * 384

@pytest.fixture(autouse=True)
def fake_models_module(monkeypatch):
    # Create a fake `models` module with Project and ProjectVector
    fake = types.ModuleType('models')
    class FakeProject:
        def __init__(self):
            self.id = 1
            self.title = 'Fake'
            self.url = 'http://example.com'
            self.description = 'fake'

    class FakePV:
        def __init__(self, proj=None, emb=None):
            self.project = proj or FakeProject()
            self.embedding = emb

    class FakeQuery:
        def join(self, *args, **kwargs):
            # Return object with .all() that returns empty list (no rows)
            return types.SimpleNamespace(all=lambda: [])

    fake.Project = FakeProject
    fake.ProjectVector = types.SimpleNamespace(query=FakeQuery())

    sys.modules['models'] = fake
    yield
    # cleanup
    try:
        del sys.modules['models']
    except KeyError:
        pass


def test_check_novelty_missing_description():
    client = app.test_client()
    resp = client.post('/api/check_novelty', json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_check_novelty_with_dummy_model(monkeypatch):
    # Patch embedding model to avoid heavy model load
    monkeypatch.setattr('app._embedding_model', DummyModel())

    client = app.test_client()
    resp = client.post('/api/check_novelty', json={'description': 'Test idea'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'novelty_score' in data
    assert isinstance(data['novelty_score'], float)
    assert 'similar_projects' in data
    assert isinstance(data['similar_projects'], list)
