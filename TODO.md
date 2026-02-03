# TODO: Fix ReviewQueue.jsx Issues

## 1. Color System Mismatch
- [ ] Globally replace all `gray-*` classes with `neutral-*` to match design rules

## 2. Hallucination Risk Semantic Emphasis
- [ ] Add conditional color mapping for `hallucination_risk_level`:
  - Low: `text-green-400`
  - Medium: `text-yellow-400`
  - High: `text-red-400`
  - Default: `text-neutral-400`

## 3. Feedback Flags Density Signal
- [ ] Enhance `formatFeedbackFlags` function to add severity labels:
  - If `hallucinated_source >= 3`, add 'High hallucination risk'
  - If `weak_novelty >= 2`, add 'High novelty weakness' (assuming similar logic)

## 4. Error Handling
- [ ] Add `error` state: `const [error, setError] = useState(null);`
- [ ] Display error message: `{error && <div className="mb-4 text-sm text-red-400">{error}</div>}`
- [ ] Update `fetchIdeas` to set error on failure
- [ ] Update `handleVerdict` to set error on failure
- [ ] Clear error on successful operations
