"""Keyword extraction helpers for retrieval query generation.

Implements a lightweight TF-IDF-style scorer over unigrams/bigrams/trigrams
using in-query term frequency and static IDF priors.
"""

from __future__ import annotations

import math
import re
from collections import Counter

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "of", "on", "or", "the", "to",
    "was", "will", "with", "that", "this", "have", "do", "does",
    "did", "which", "who", "when", "where", "why", "how", "using",
}

GENERIC_TERMS = {
    "help", "helps", "develop", "develops", "create", "creates",
    "build", "builds", "make", "makes", "provide", "provides",
    "support", "manage", "enable", "improve", "enhance", "many",
    "individuals", "people", "users", "solution", "system", "platform",
    "application", "app", "based", "approach", "method",
}

# Higher weight means stronger technical discriminative value.
DOMAIN_TECHNICAL_VOCAB = {
    "constraint": 9,
    "scheduling": 9,
    "constraint scheduling": 10,
    "spatial optimization": 10,
    "layout optimization": 9,
    "resource allocation": 9,
    "federated learning": 10,
    "transformer": 8,
    "attention": 8,
    "graph neural": 9,
    "drug discovery": 9,
    "anomaly detection": 8,
    "time series": 8,
    "recommendation": 7,
    "recommender": 7,
    "nlp": 7,
    "natural language": 8,
    "interview simulator": 8,
    "resume parser": 8,
    "predictive maintenance": 9,
    "iot": 7,
    "sensor networks": 8,
    "distributed systems": 8,
    "microservices": 7,
    "event management": 7,
    "marketplace": 6,
}

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+-]*")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _build_candidates(tokens: list[str]) -> Counter:
    candidates = Counter()

    for token in tokens:
        candidates[token] += 1

    for i in range(len(tokens) - 1):
        candidates[f"{tokens[i]} {tokens[i + 1]}"] += 1

    for i in range(len(tokens) - 2):
        candidates[f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}"] += 1

    return candidates


def _is_valid_term(term: str, extra_stop_words: set[str] | None = None) -> bool:
    parts = term.split()
    merged_stop_words = STOP_WORDS | GENERIC_TERMS
    if extra_stop_words:
        merged_stop_words |= {w.lower() for w in extra_stop_words}

    if len(parts) == 1:
        token = parts[0]
        if len(token) <= 3:
            return False
        if token in merged_stop_words:
            return False
        return True

    # For phrases, reject if all tokens are low-value.
    return any(len(p) > 3 and p not in merged_stop_words for p in parts)


def _estimate_document_frequency(term: str) -> float:
    vocab_weight = DOMAIN_TECHNICAL_VOCAB.get(term, 0)
    if vocab_weight > 0:
        # Weighted terms are assumed rarer in a corpus.
        return max(5.0, 140.0 - vocab_weight * 10.0)

    token_count = len(term.split())
    if token_count >= 3:
        return 45.0
    if token_count == 2:
        return 90.0
    return 220.0


def extract_key_terms_tfidf(
    query: str,
    max_terms: int = 5,
    extra_stop_words: set[str] | None = None,
) -> list[str]:
    """Extract key terms using a lightweight TF-IDF-like scoring strategy."""
    if not query:
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    candidates = _build_candidates(tokens)

    scored = []
    pseudo_corpus_docs = 2000.0
    for term, tf in candidates.items():
        if not _is_valid_term(term, extra_stop_words=extra_stop_words):
            continue

        df = _estimate_document_frequency(term)
        idf = math.log((pseudo_corpus_docs + 1.0) / (df + 1.0)) + 1.0

        phrase_bonus = 1.25 if len(term.split()) > 1 else 1.0
        vocab_bonus = 1.0 + (DOMAIN_TECHNICAL_VOCAB.get(term, 0) / 12.0)
        length_bonus = min(len(term) / 25.0, 0.6)

        score = float(tf) * idf * phrase_bonus * vocab_bonus + length_bonus
        scored.append((term, score))

    if not scored:
        return []

    # Prefer higher-scoring candidates and reduce near-duplicates.
    scored.sort(key=lambda item: item[1], reverse=True)
    selected = []
    selected_token_sets = []

    for term, _ in scored:
        term_tokens = set(term.split())

        # Skip terms that are effectively subsets of existing selections.
        if any(term_tokens.issubset(existing) for existing in selected_token_sets):
            continue

        selected.append(term)
        selected_token_sets.append(term_tokens)
        if len(selected) >= max_terms:
            break

    return selected
