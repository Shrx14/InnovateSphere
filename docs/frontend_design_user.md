# Frontend Design Rules — InnovateSphere (User Interface)

> **Scope:**
> This document applies **ONLY** to user-facing screens (logged-out and logged-in users).
>
> **Admin UI is explicitly excluded** and must continue using `frontend_design_admin.md`.
>
> **Last updated:** 2026-03-04 — reflects implemented design decisions and all features.

---

## 0. Design Intent

InnovateSphere's user interface should feel:

* Serious, not playful
* Modern, not trendy
* Research-first, not AI-demo-first
* Calm, not visually loud

The UI draws from **Formless / Deepgram–style product UX**:

* restrained motion
* strong typography rhythm
* evidence-forward layouts
* minimal but intentional branding

**Implemented refinements:**
The production UI adopts controlled visual enhancements beyond flat design — subtle gradients, glow borders, and starfield backgrounds — to reinforce the product's brand identity as an innovative research tool. These effects are intentional and scoped: they enhance the premium feel without crossing into "AI playground" territory.

---

## 1. Hard Separation Rules (MANDATORY)

* **User UI uses `UserShell.jsx`**
* **Admin UI uses `AdminShell.jsx`**
* **Public UI uses `PublicShell.jsx`**
* User UI **may import brand styles**
* Admin UI **must never import brand styles**
* Shared components must be visually neutral

Violation of these rules is an **architectural bug**, not a design choice.

---

## 2. Color System (User UI)

### Base (dark system default)

* Background: `bg-neutral-950`
* Primary surface: `bg-neutral-900`
* Elevated surface: `bg-neutral-800`
* Borders: `border-neutral-800`
* Divider lines: `border-neutral-700`

---

### Brand Accent

**Primary:** Slate–Indigo

* Accent text: `text-indigo-400`
* Accent border: `border-indigo-500/40`
* Accent background (rare): `bg-indigo-600/10`

**Implemented brand enhancements:**

* Gradient text for hero headings: `bg-gradient-to-r from-indigo-400 to-purple-400` (Landing, Header)
* Glow border on feature cards: `.glow-border`, `.glow-border-pulse` classes (Generate, Explore, Dashboard, Novelty)
* Card shine effect: `.card-shine` for premium card surfaces
* Starfield background: `StarfieldBackground.jsx` for immersive dark-mode atmosphere (User and Public shells)

#### Accent Usage Rules

* Accent color must not exceed **15–20% of a screen**
* Accent is used for: focus, emphasis, primary action, and brand reinforcement
* Gradients are restricted to: headings, hero sections, nav logos, and chart fills
* Glow borders are restricted to: primary content cards and interactive surfaces
* Neither gradients nor glows appear in body text, metadata, or data tables

---

## 3. Typography System (User UI)

### Font Family

* System font stack only (`font-sans`)
* No custom fonts
* No web fonts

### Typography Feel

Achieved through **weight, spacing, and rhythm**, not font choice.

---

### Heading Hierarchy

* **H1**
  `text-5xl font-light tracking-tight text-white`

* **H2**
  `text-3xl font-normal text-white`

* **H3**
  `text-xl font-medium text-neutral-200`

* **Section labels**
  `text-xs uppercase tracking-widest text-neutral-400`

### Body Text

* Primary body
  `text-base text-neutral-300 leading-relaxed`

* Secondary body
  `text-sm text-neutral-400`

* Metadata / captions
  `text-xs text-neutral-500`

---

## 4. Layout & Spacing Rhythm (CRITICAL)

User UI must feel **spacious and intentional**, unlike admin UI.

### Page Structure (MANDATORY)

Every page must follow this vertical rhythm:

1. **Intent section**
   Explains what this page is about

2. **Primary content**
   Main user task

3. **Secondary insight**
   Supporting data or explanation

4. **Optional action**
   CTA or navigation

---

### Spacing Rules

* Section spacing: `mb-20`
* Card padding: `p-8`
* Grid gap: `gap-8`
* Internal element spacing: `space-y-4` or `space-y-6`

Avoid tight layouts. If it feels dense, it's wrong.

---

## 5. Motion System (User UI Only)

Motion is allowed, **but tightly controlled**.

### Allowed Animations

* Opacity fade-in
* TranslateY up to **8px**
* Duration: **250–400ms**
* Easing: `ease-out`
* Subtle scale interactions on interactive elements (`whileHover/whileTap` with max scale 1.03)
* Glow pulse on featured cards (CSS keyframe, subtle)

### Where Motion is Allowed

* Page entry
* Section reveal
* List population
* Interactive card hover (subtle scale ≤ 1.03 + translateY ≤ -2px)
* Starfield background (ambient, low-opacity)

### Where Motion is FORBIDDEN

* Infinite attention-grabbing loops at high opacity
* Scroll-jacking or scroll-tied parallax
* Chart data point animations
* Button bouncing or shaking

**Rule:**
Motion should feel like content *settling*, with controlled hover feedback on interactive surfaces.

---

## 6. Cards & Surfaces (Signature Look)

### Standard Card

```jsx
className="
  bg-neutral-900
  border border-neutral-800
  rounded-2xl
  p-8
"
```

### Featured Card (brand-enhanced)

```jsx
className="
  bg-neutral-900
  border border-neutral-800
  rounded-2xl
  p-8
  glow-border
"
```

Optional (sparingly):

* `bg-neutral-900/80`
* `backdrop-blur-sm`
* `card-shine` — single shimmer overlay for premium feel

### Forbidden

* Heavy shadows (`shadow-xl`, `shadow-2xl`)
* Rainbow or multi-hue gradients
* Border color cycling animations

---

## 7. Buttons (User UI Variant)

### Primary Action

```jsx
className="
  bg-indigo-600/90
  hover:bg-indigo-600
  text-white
  rounded-lg
  px-6 py-3
  font-medium
  transition-colors
"
```

### Secondary Action

```jsx
className="
  border border-neutral-700
  text-neutral-300
  rounded-lg
  px-6 py-3
  hover:border-neutral-500
"
```

### Button Rules

* No bouncing or shaking transforms
* No glowing outlines on buttons
* Focus state must be visible

---

## 8. Data & Trust Presentation

User UI must **prioritize credibility** over excitement.

### Trust Signals

* Text-first
* Visual indicators second
* Icons for quick-reaction feedback (Lucide icons or emoji for compact reactions)
* Score display: 0–10 scale via `formatScore()` (internal 0–100, displayed as `/10`)

Examples:

* "Novelty: High (7.8/10)"
* "Evidence strength: Medium"
* "Reviewed by community"

No gamification. No progress meters without explanation.

---

## 9. Feature Inventory (Implemented)

### Core Features

| Feature | Route | Component | Status |
|---------|-------|-----------|--------|
| Landing Page | `/` | `LandingPage` | Done |
| Explore/Browse | `/explore` | `ExplorePage` | Done |
| Login / Register | `/login`, `/register` | `LoginPage`, `RegisterPage` | Done |
| User Dashboard | `/user/dashboard` | `UserDashboard` | Done |
| Idea Generation | `/user/generate` | `GeneratePage` | Done |
| Novelty Analysis | `/user/novelty` | `NoveltyPage` | Done |
| Idea Detail | `/idea/:id` | `IdeaDetail` | Done |
| User Profile | `/user/profile` | `UserProfilePage` | Done |
| Admin Review | `/admin/review` | `AdminReviewQueue` | Done |
| Admin Idea Detail | `/admin/idea/:id` | `AdminIdeaDetail` | Done |
| Admin Analytics | `/admin/analytics` | `AdminAnalytics` | Done |
| Admin Abuse | `/admin/abuse` | `AdminAbuseEvents` | Done |

### User Actions on Ideas

| Action | Implementation |
|--------|---------------|
| Bookmark toggle | `POST/DELETE /api/ideas/:id/feedback` with `feedback_type: "bookmark"` |
| Share (copy link) | Clipboard copy via `navigator.clipboard.writeText()` + toast |
| Request idea (track demand) | `POST /api/ideas/:id/request` — demand count displayed on detail page |
| Rate (1–5 stars) | `POST /api/ideas/:id/review` — upsert per user |
| Quick reactions | `POST /api/ideas/:id/feedback` — upvote, downvote, helpful, not_helpful |
| Quality feedback | `POST /api/ideas/:id/feedback` — factual_error, hallucinated_source, weak_novelty, etc. |

### Notification Mechanisms

| Mechanism | Used Where |
|-----------|-----------|
| Toast (Sonner) | Feedback, review, bookmark, share, admin actions |
| SSE streaming | Idea generation progress (with polling fallback) |
| Inline error banners | Form validation, API errors |
| Loading skeletons | All data-loading states |

---

## 10. Page-Specific Guidelines

### Landing Page

* Bold hero with gradient heading (brand reinforcement)
* Live platform stats from public API
* Top ideas showcase with glow-border cards
* Charts showing platform activity (area/radar)
* Starfield background for atmosphere

### Explore Page

* Discovery-focused layout
* Domain filter bar with active state highlighting
* Cards emphasize **problem statement**, scores secondary
* Pagination with page size control

### Idea Detail Page

Order of importance:

1. Problem & context
2. Evidence & sources (tiered: Supporting / Contextual / Peripheral)
3. Trust & quality signals (novelty score, quality score, evidence strength)
4. User actions (bookmark, share, request, review, feedback)
5. Metadata (views, timestamps, domain)

### User Dashboard

* Three tabs: My Ideas, Bookmarked, Activity
* Stats overview cards with glow borders
* Sort/filter on idea lists
* Gentle entry motion

### Generate Page

* Domain selection grid then text query input
* Real-time SSE progress: phase name, progress bar, source count, novelty score
* Completion card with shine effect
* "View Full Details" navigation on success

### Novelty Page

* Description input + domain selector
* Synchronous analysis (no background job)
* Score card with level badge, confidence, evidence score
* Tiered source list (Supporting / Contextual / Peripheral)
* Insights key-value breakdown

### User Profile Page

* View/edit: username, skill level, preferred domain
* Password change with current password verification
* JWT re-issued on profile update

---

## 11. Forbidden Patterns (User UI)

* No AI chat UI patterns
* No prompt-centric layouts
* No rainbow or multi-hue gradients
* No neon color palettes
* No scroll-jacking
* No decorative charts without data meaning
* No gamification (XP, badges, streaks)

If it feels like a generic AI demo or gaming interface, revise.

---

## 12. Consistency Rules

* Every metric must mean something
* Every section must answer a question
* Scores always displayed in 0–10 scale via `formatScore()` (backend stores 0–100)
* Decorative UI without meaning is not allowed
* If unsure, **remove, don't add**

---

## 13. Enforcement

* This document is mandatory for all user UI work
* Deviations require written justification
* Admin UI rules remain untouched
* Brand styles must never leak into admin surfaces

---

## 14. Final Design Check (Before Shipping)

Ask:

* Does this feel serious?
* Does this feel research-grade?
* Does this feel calm?
* Does this feel premium without being flashy?

If any answer is "no", revise.

