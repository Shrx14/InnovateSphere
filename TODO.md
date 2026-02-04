# Cosine Similarity Implementation Task

## Tasks
- [x] Update `_cosine_similarity` function in `backend/semantic/filter.py` to use the exact formula: `den = np.linalg.norm(a) * np.linalg.norm(b); sim = np.dot(a, b) / den if den else 0.0`
