# Frontend Implementation Plan for InnovateSphere

## Phase 0 - Structural Foundations
- [x] Verify UserShell.jsx and AdminShell.jsx exist
- [x] Confirm routing split: /admin/* → AdminShell, /* → UserShell
- [x] Update UserShell to use neutral color system (bg-neutral-950, etc.) per frontend_design_user.md
- [x] Update LandingPage to remove forbidden gradient and update buttons to indigo accent per user design
- [x] Add missing routes to App.jsx: /login, /register, /idea/:id, /generate, /admin/idea/:id
- [x] Create GeneratePage.jsx for /generate route
- [x] Create AdminIdeaDetail.jsx for /admin/idea/:id route

## Phase 1 - API Alignment
- [ ] Verify/assume backend endpoints exist as listed in plan
- [ ] Update components to use correct API calls (e.g., /api/public/*, /api/ideas/*, /api/admin/*)
- [ ] Define frontend data contracts as per plan examples

## Phase 3 - User Brand Surface (Public + Auth)
- [ ] Landing Page: Remove gradient, novelty preview, prompt box; add subtle entrance animation; structure with HeroStatBlock, DomainOverview, TopIdeasPreview; consume /api/public/stats, /api/public/top-domains, /api/public/top-ideas
- [ ] Explore Page: Remove novelty/quality scores; implement card skeleton with vertical rhythm; titles dominate, problem statement preview; domain filter, keyword search, real pagination; consume /api/public/ideas
- [ ] Idea Detail Page: Logged-out view (title, problem statement, tech stack, sources, view count); logged-in view (add novelty explanation, quality score, evidence strength, hallucination risk, feedback actions); enforce section priority order; consume /api/public/ideas/:id or /api/ideas/:id
- [ ] Brand Compliance: Apply neutral color system, typography hierarchy, spacing rhythm, allowed motion (single entrance animation on mount)

## Phase 2+ - Full UI Implementation
- [ ] Ensure all user pages follow frontend_design_user.md (neutral colors, typography, etc.)
- [ ] Ensure all admin pages follow frontend_design_admin.md (gray colors, etc.)
- [ ] Implement auth handling for logged-in vs logged-out states
- [ ] Add motion and interactions per user design (restrained)
- [ ] Test and refine UX for Formless/Deepgram-style experience
