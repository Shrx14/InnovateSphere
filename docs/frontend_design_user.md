# Frontend Design Rules — InnovateSphere (User Interface)

> **Scope:**
> This document applies **ONLY** to user-facing screens (logged-out and logged-in users).
>
> **Admin UI is explicitly excluded** and must continue using `frontend_design_admin.md`.

---

## 0. Design Intent

InnovateSphere’s user interface should feel:

* Serious, not playful
* Modern, not trendy
* Research-first, not AI-demo-first
* Calm, not visually loud

The UI should resemble **Formless / Deepgram–style product UX**:

* restrained motion
* strong typography rhythm
* evidence-forward layouts
* minimal but intentional branding

If a screen feels like a **marketing site or AI playground**, it is incorrect.

---

## 1. Hard Separation Rules (MANDATORY)

* **User UI uses `UserShell.jsx`**
* **Admin UI uses `AdminShell.jsx`**
* User UI **may import brand styles**
* Admin UI **must never import brand styles**
* Shared components must be visually neutral

Violation of these rules is an **architectural bug**, not a design choice.

---

## 2. Color System (User UI)

### Base (inherits neutral dark system)

* Background: `bg-neutral-950`
* Primary surface: `bg-neutral-900`
* Elevated surface: `bg-neutral-800`
* Borders: `border-neutral-800`
* Divider lines: `border-neutral-700`

These are the **default colors**. Do not decorate them.

---

### Brand Accent (SINGLE accent only)

Choose **one accent color globally** and do not mix accents.

**Recommended:** Slate–Indigo

* Accent text: `text-indigo-400`
* Accent border: `border-indigo-500/40`
* Accent background (rare): `bg-indigo-600/10`

#### Accent Usage Rules

* Accent color must not exceed **10–15% of a screen**
* Accent is used for:

  * focus
  * emphasis
  * primary action
* Accent is **not decorative**

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

Avoid tight layouts. If it feels dense, it’s wrong.

---

## 5. Motion System (User UI Only)

Motion is allowed, **but tightly controlled**.

### Allowed Animations

* Opacity fade-in
* TranslateY up to **8px**
* Duration: **250–400ms**
* Easing: `ease-out`

### Where Motion is Allowed

* Page entry
* Section reveal
* List population

### Where Motion is FORBIDDEN

* Buttons
* Cards on hover
* Charts
* Infinite loops
* Scroll-tied motion
* Decorative motion

**Rule:**
Motion should feel like content *settling*, not reacting.

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

Optional (sparingly):

* `bg-neutral-900/80`
* `backdrop-blur-sm`

### Forbidden

* Heavy shadows (`shadow-xl`, `shadow-2xl`)
* Glows
* Gradients
* Border animations

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

* No scale or transform effects
* No glowing outlines
* Focus state must be visible

---

## 8. Data & Trust Presentation

User UI must **prioritize credibility** over excitement.

### Trust Signals

* Text-first
* Visual indicators second
* Never emoji-based
* Icons optional, minimal

Examples:

* “Novelty: High (78/100)”
* “Evidence strength: Medium”
* “Reviewed by community”

No gamification. No progress meters without explanation.

---

## 9. Page-Specific Guidelines

### Landing Page

* Calm hero (no prompt box)
* Clear explanation of how system works
* Credibility before CTA
* Minimal motion

### Explore Page

* Discovery-focused
* Filters feel analytical
* Cards emphasize **problem statement**, not scores
* Scores are secondary

### Idea Detail Page

Order of importance:

1. Problem & context
2. Evidence & sources
3. Trust & quality signals
4. Metadata (views, timestamps)

### User Dashboard

* Feels like ownership
* Shows progress & status
* Gentle entry motion allowed
* No charts unless they explain decisions

---

## 10. Forbidden Patterns (User UI)

* ❌ Emojis
* ❌ AI chat UI patterns
* ❌ Prompt-centric layouts
* ❌ Gradients
* ❌ Neon or glow effects
* ❌ Infinite animations
* ❌ Decorative charts

If it feels like an AI demo, remove it.

---

## 11. Consistency Rules

* Every metric must mean something
* Every section must answer a question
* Decorative UI without meaning is not allowed
* If unsure, **remove, don’t add**

---

## 12. Enforcement

* This document is mandatory for all user UI work
* Deviations require written justification
* Admin UI rules remain untouched
* Brand styles must never leak into admin surfaces

---

## 13. Final Design Check (Before Shipping)

Ask:

* Does this feel serious?
* Does this feel research-grade?
* Does this feel calm?
* Does this feel different from generic AI tools?

If any answer is “no”, revise.

