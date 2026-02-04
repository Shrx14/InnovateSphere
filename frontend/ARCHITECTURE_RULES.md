# InnovateSphere — Frontend Architecture Rules

These rules are NON-NEGOTIABLE.

## UI Separation
- Admin UI = core UI only (dense, functional, zero brand)
- User UI = core UI + brand surface

## Import Boundaries
Admin UI MUST NOT import:
- Brand styles
- Animated components
- Marketing UI
- User-only components

User UI MUST NOT import:
- Admin moderation components
- Governance widgets
- Admin-only layouts

## Layout Enforcement
- All admin routes MUST render inside AdminShell
- All user routes MUST render inside UserShell
- No shared global layout

## Philosophy
Admin UI should feel boring but powerful.
User UI should feel modern but serious.

If a future change violates this file, the change is WRONG.
