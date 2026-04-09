#!/usr/bin/env python3
"""Build a FAISS reference index from a JSONL corpus.

Each JSONL row should include a text field (default: `text`) and optional id field.
Example row:
{"id": "paper-1", "text": "Transformer methods for ..."}
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from backend.evaluation.faiss_index import FaissReferenceIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("build_faiss_reference_index")


def _read_jsonl(path: Path, *, text_key: str, id_key: str) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    ids: list[str] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                logger.warning("Skipping invalid JSONL row at line %d", line_no)
                continue

            if not isinstance(payload, dict):
                continue

            text = payload.get(text_key)
            if not isinstance(text, str) or not text.strip():
                continue

            text = text.strip()
            texts.append(text)
            ids.append(str(payload.get(id_key, len(ids))))

    return texts, ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAISS reference index from JSONL")
    parser.add_argument("--input-jsonl", required=True, help="Path to source JSONL file")
    parser.add_argument("--index-out", required=True, help="Output path for FAISS index file")
    parser.add_argument("--metadata-out", required=True, help="Output path for metadata JSON file")
    parser.add_argument("--text-key", default="text", help="JSON key containing source text")
    parser.add_argument("--id-key", default="id", help="JSON key containing stable id")
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {input_path}")

    texts, ids = _read_jsonl(input_path, text_key=args.text_key, id_key=args.id_key)
    if not texts:
        raise RuntimeError("No valid text rows found in input corpus")

    logger.info("Loaded %d texts. Building embeddings and FAISS index...", len(texts))
    index = FaissReferenceIndex.from_texts(texts, ids=ids)

    index.save(index_path=args.index_out, metadata_path=args.metadata_out)
    logger.info("Saved index to %s", args.index_out)
    logger.info("Saved metadata to %s", args.metadata_out)
    logger.info("Index dimension=%d, vectors=%d", index.dimension, index.index.ntotal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
