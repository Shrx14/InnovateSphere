# Phase 6: Polish & Consistency - TODO

## Motion Audit Refinement
- [ ] Remove demo leftovers: Delete App-logo-spin @keyframes from App.css
- [ ] Refine LandingPage.jsx: Keep hero entrance, primary sections entrance; remove minor text animations
- [ ] Refine ExplorePage.jsx: Keep subtle list entrance; remove filters/pagination animations
- [ ] Refine IdeaDetail.jsx: Keep page entrance; remove section-by-section animations
- [ ] Refine UserDashboard.jsx: Remove per-card Framer Motion; keep single container entrance
- [ ] Remove framer-motion dependency if no longer needed after refinements

## Information Density Audit
- [ ] Audit LandingPage: Ensure sections answer user questions; remove fluff if any
- [ ] Audit ExplorePage: Ensure answers "what ideas/how different/which matter"; add ranking if missing
- [ ] Audit IdeaDetail: Confirm answers required questions
- [ ] Audit UserDashboard: Keep novelty/quality where they explain status; remove non-actionable metrics
- [ ] Audit Admin ReviewQueue: Confirm zero brand motion, answers admin questions
- [ ] Purge placeholders: Remove any "coming soon", fake metrics, static charts

## Final Checks
- [ ] Verify total UI code decreased
- [ ] Confirm motion doesn't hide content/repeat without action/exist without data change
- [ ] Confirm every number affects a decision, zero decorative content
- [ ] Ensure site feels quieter, more serious, product-grade
