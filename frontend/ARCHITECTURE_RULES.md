# InnovateSphere — Frontend Architecture Rules

These rules are NON-NEGOTIABLE.

## UI Separation
- Admin UI = core UI only (dense, functional, zero brand) refer to /docs/frontend_design_admin.md
- User UI = core UI + brand surface refer to /docs/frontend_design_user.md


## Layout Enforcement
- All admin routes MUST render inside AdminShell
- All user routes MUST render inside UserShell
- No shared global layout

## Philosophy
Admin UI should feel boring but powerful.
User UI should feel modern but serious.

If a future change violates this file, the change is WRONG.
