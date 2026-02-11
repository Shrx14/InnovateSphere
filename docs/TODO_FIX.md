# Fix for "No relevant sources found" Error

## Problem
- arXiv returns 10 sources successfully
- Semantic filter with threshold 0.6 removes all sources (similarity scores too low)
- Fallback logic should use all sources, but error still occurs
- Need to add better logging and fix edge cases

## Steps

### 1. Fix backend/generation/generator.py
- [x] Add detailed logging to trace source flow
- [x] Fix empty sources check to handle edge cases
- [x] Ensure fallback logic works when semantic filter removes all sources
- [x] Add similarity scores to logs for debugging


### 2. Verify backend/semantic/ranker.py
- [x] Confirmed ranker doesn't filter, only sorts

## Root Cause Analysis
The error "No sources found for topic" occurs at line 168 in generator.py. The check `if not retrieved or 'sources' not in retrieved` may not be catching all edge cases where sources are empty or invalid.
