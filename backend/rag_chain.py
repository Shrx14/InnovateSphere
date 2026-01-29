# Optional heavy dependency; handle gracefully if missing
try:
    import torch
except Exception as _e:
    torch = None
    print(f"⚠️ Warning: optional module 'torch' not available: {_e}")
import os
try:
    from backend.config import Config
except ImportError:
    from config import Config
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

# --- 1. Define Constants (Must match your 40% setup) ---
EMBEDDING_MODEL_NAME = Config.EMBEDDING_MODEL
COLLECTION_NAME = 'arxiv_papers'
DATABASE_URL = Config.RAG_DATABASE_URL or Config.DATABASE_URL


def _sanitize_database_url(url: str) -> str:
    """Remove known problematic query params (like channel_binding) from DATABASE_URL.

    Some managed Postgres poolers (e.g. Neon) set `channel_binding=require` which
    can lead to unexpected SSL connection closures from certain client stacks.
    This helper removes that param as a pragmatic workaround while keeping
    `sslmode` when present.
    """
    if not url or '?' not in url:
        return url
    base, qs = url.split('?', 1)
    parts = [p for p in qs.split('&') if not p.startswith('channel_binding=')]
    if not parts:
        return base
    return base + '?' + '&'.join(parts)

# --- 2. Load the Generative Model (LLM) ---
# This one line replaces the entire transformers pipeline setup
llm = Ollama(model=Config.OLLAMA_MODEL, base_url=Config.OLLAMA_BASE_URL)

# --- 3. Load the Embedding Model and Vector Store ---
# Load the same embedding model used in your data_pipeline.py
try:
    embedding_function = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
except Exception as _e:
    embedding_function = None
    print(f"⚠️ Warning: embedding model couldn't be initialized: {_e}")

# Lazy-init placeholders (avoid connecting to DB at import time)
vector_store = None
qa_chain = None

def init_rag_chain():
    """Initialize PGVector and the QA chain. Safe to call multiple times."""
    global vector_store, qa_chain
    if qa_chain is not None:
        return
    try:
        # Try connecting with the provided DATABASE_URL first
        try:
            vector_store = PGVector(
                connection_string=DATABASE_URL,
                embedding_function=embedding_function,
                collection_name=COLLECTION_NAME,
                use_jsonb=True,
            )
        except Exception as first_err:
            # If the DB URL contains channel_binding it can cause SSL closures
            # with some client stacks. Retry with a sanitized URL as a fallback.
            sanitized = _sanitize_database_url(DATABASE_URL)
            if sanitized != DATABASE_URL:
                print(f"Warning: initial PGVector init failed; retrying with sanitized DATABASE_URL: {first_err}")
                vector_store = PGVector(
                    connection_string=sanitized,
                    embedding_function=embedding_function,
                    collection_name=COLLECTION_NAME,
                    use_jsonb=True,
                )
            else:
                raise
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True,
        )
        print("✅ RAG Chain Initialized Successfully!")
    except Exception as e:
        print(f"⚠️ Warning: RAG Chain initialization failed (DB or vector store issue): {e}")
        vector_store = None
        qa_chain = None

# --- 4. Define the Prompt Template ---
# THIS IS A CRITICAL CHANGE
# Mistral requires a specific instruction format
template = """
<s>[INST] You are an AI assistant for a platform called InnovateSphere.
Your job is to generate a new, creative project idea for a student, based on their query.
Use the following pieces of context from research papers to inspire the idea.
The idea should be structured as follows:

Problem Statement: [A concise description of the problem the project aims to solve]
Tech Stack: [A list of recommended technologies or frameworks for the project]
Uniqueness: [A short description of why this project idea is unique or innovative]
Project Description: [A single, concise paragraph describing the project idea]

CONTEXT: {context}

QUERY: {question} [/INST]

GENERATED IDEA:
"""
PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

# --- 5. Create the RAG Chain ---
# Initialization is performed lazily via `init_rag_chain()` to avoid
# failing the import when the database or vector store is unavailable.
# Call `init_rag_chain()` before using the RAG chain.

def generate_idea(query):
    """
    Takes a user query and returns a generated project idea.
    """
    print(f"Generating idea for query: {query}")
    # Ensure RAG chain is initialized (will attempt to connect lazily)
    init_rag_chain()

    # If the QA chain is available, use it (retrieval-augmented generation)
    if qa_chain is not None:
        try:
            # Call the chain with a dict input so it returns a structured
            # output (including `source_documents`) when `return_source_documents=True`.
            result = qa_chain({"query": query})

            # Normalise possible return formats
            if isinstance(result, str):
                return {"result": result, "source_documents": []}
            # Some chain implementations may return 'answer' instead of 'result'
            if isinstance(result, dict) and 'answer' in result and 'result' not in result:
                result['result'] = result.pop('answer')

            src_docs = result.get('source_documents') or []
            print(f"RAG returned {len(src_docs)} source documents.")

            # If the RAG chain returned no source documents, attempt a DB-backed
            # similarity lookup against the already-ingested `projects` table so
            # the frontend can still show 'inspired by' cards.
            if not src_docs:
                try:
                    print('No source docs from RAG; performing DB fallback retrieval...')
                    # Lazy-import to avoid circular app startup issues
                    from app import app
                    from models import Project, ProjectVector
                    import numpy as np
                    # Try to instantiate a local sentence-transformers model
                    try:
                        from sentence_transformers import SentenceTransformer
                        emb_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                    except Exception as e:
                        emb_model = None
                        print('Embedding fallback model unavailable:', e)

                    query_text = query if isinstance(query, str) else str(query)
                    if emb_model is not None:
                        q_emb = emb_model.encode(query_text)
                        q_arr = np.array(q_emb, dtype=float)

                        # Fetch vectors from DB and compute cosine similarity inside app context
                        with app.app_context():
                            rows = ProjectVector.query.join(Project).all()
                            sims = []
                            for pv in rows:
                                # Avoid ambiguous truth-value checks on numpy arrays
                                if pv.embedding is None:
                                    continue
                                try:
                                    if hasattr(pv.embedding, '__len__') and len(pv.embedding) == 0:
                                        continue
                                except Exception:
                                    # If checking length fails, skip this vector
                                    continue
                                try:
                                    emb = np.array(pv.embedding, dtype=float)
                                    denom = (np.linalg.norm(emb) * np.linalg.norm(q_arr))
                                    cos = float(np.dot(emb, q_arr) / denom) if denom != 0 else 0.0
                                except Exception:
                                    cos = 0.0
                                sims.append((pv.project, cos))

                        sims.sort(key=lambda x: x[1], reverse=True)
                        top = sims[:5]
                        src_docs = []
                        for proj, score in top:
                            src_docs.append(type('SD', (), {
                                'metadata': {'title': proj.title, 'url': proj.url},
                                'page_content': (proj.description or '')
                            })())
                        # Attach to result for frontend consumption
                        result['source_documents'] = src_docs
                        print(f'Fallback returned {len(src_docs)} source documents from DB.')
                except Exception as db_fallback_err:
                    print('DB fallback retrieval failed:', db_fallback_err)

            return result
        except Exception as e:
            print(f"Error running QA chain: {e}")

    # Fallback: if retrieval or LLM fails, produce a simple template-based idea
    try:
        # Try LLM only if available
        if llm is not None:
            formatted = PROMPT.format(context="No context available", question=query)
            try:
                llm_resp = llm(formatted)
                if isinstance(llm_resp, dict):
                    text = llm_resp.get('text') or llm_resp.get('result') or str(llm_resp)
                else:
                    text = str(llm_resp)
                return {"result": text, "source_documents": []}
            except Exception as llm_err:
                print(f"LLM call failed: {llm_err} — falling back to template generator.")
        # Deterministic template fallback (no external dependencies)
        title = f"{query.strip()[:60]}"
        problem = f"Build a small project that addresses {query.strip().lower()} in a practical, beginner-friendly way."
        tech = "Frontend: React, Backend: Flask, Storage: PostgreSQL, AI: sentence-transformers or a simple REST API"
        uniqueness = "Focus on simplicity, clear tutorials, and reproducible datasets for learners."
        description = (
            f"Problem Statement: {problem}\n"
            f"Tech Stack: {tech}\n"
            f"Uniqueness: {uniqueness}\n"
            f"Project Description: A beginner-friendly web app that demonstrates how to integrate basic AI features (like novelty checking or simple recommendations) into a practical project. The app should include step-by-step setup instructions, example data, and a simple UI to explore results."
        )
        return {"result": description, "source_documents": []}
    except Exception as e:
        print(f"Fallback generator failed: {e}")
        return {"result": "Service unavailable. Please try again later.", "source_documents": []}


# Example test (optional)
if __name__ == "__main__":
    print("--- Testing RAG Chain ---")
    test_query = "A beginner web app using AI"
    idea = generate_idea(test_query)
    print(f"Test Query: {test_query}")
    print(f"Generated Idea: {idea['result']}")
    print(f"Source Documents Used: {len(idea['source_documents'])}")
