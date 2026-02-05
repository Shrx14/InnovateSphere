# Frontend Design Rules - InnovateSphere

## Overview
These design rules establish visual constraints for InnovateSphere's frontend for admin. The design system prioritizes accessibility, consistency, and maintainability with a dark-first approach and neutral color palette.

## Color Palette

### Primary Colors (Dark-First)
- **Background**: `bg-gray-900` (dark slate) - Primary background for all components
- **Surface**: `bg-gray-800` (slightly lighter dark) - Cards, modals, and elevated surfaces
- **Text Primary**: `text-white` - Main text content
- **Text Secondary**: `text-gray-300` - Supporting text, labels
- **Text Muted**: `text-gray-500` - Disabled states, placeholders

### Accent Colors
- **Primary**: `text-blue-400` or `bg-blue-600` - Interactive elements, links
- **Success**: `text-green-400` - Positive states, confirmations
- **Warning**: `text-yellow-400` - Caution states
- **Error**: `text-red-400` - Error states, destructive actions

### Neutral Base
- Use grayscale palette exclusively (`gray-50` through `gray-900`)
- Avoid saturated colors except for semantic states (success, error, etc.)
- Maintain minimum contrast ratios: 4.5:1 for normal text, 3:1 for large text

## Typography Hierarchy

### Headings
- **H1**: `text-4xl font-bold text-white` - Page titles, major sections
- **H2**: `text-3xl font-semibold text-white` - Section headers
- **H3**: `text-2xl font-semibold text-white` - Subsection headers
- **H4**: `text-xl font-medium text-white` - Component titles
- **H5**: `text-lg font-medium text-gray-300` - Minor headings
- **H6**: `text-base font-medium text-gray-300` - Small headings

### Body Text
- **Primary**: `text-base text-gray-300` - Main content
- **Secondary**: `text-sm text-gray-400` - Supporting content
- **Caption**: `text-xs text-gray-500` - Metadata, timestamps

### Font Family
- Use system fonts only: `font-sans` (default Tailwind system stack)
- No custom fonts or web fonts

## Spacing System

### Use Tailwind Defaults Only
- **Margins/Padding**: `m-`, `p-` classes (0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64)
- **Gaps**: `gap-` classes for flexbox/grid layouts
- **No custom spacing values** - All spacing must use predefined Tailwind scale

### Layout Spacing Guidelines
- **Component padding**: `p-4` (16px) minimum, `p-6` (24px) preferred
- **Section spacing**: `mb-8` (32px) between major sections
- **Element spacing**: `mb-4` (16px) between related elements
- **Grid gaps**: `gap-4` (16px) for card grids, `gap-6` (24px) for spacious layouts

## Button Styles

### Primary Buttons
```jsx
className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200"
```
- Solid blue background
- White text
- Subtle hover state (darker blue)
- Standard padding and border radius

### Secondary Buttons
```jsx
className="bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium py-2 px-4 rounded-md border border-gray-600 transition-colors duration-200"
```
- Dark gray background
- Light gray text
- Subtle border
- Consistent with primary button sizing

### Button States
- **Disabled**: `opacity-50 cursor-not-allowed` - Reduce opacity, prevent interaction
- **Loading**: Add spinner, maintain button dimensions
- **Focus**: `focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900`

## Forbidden Patterns

### ❌ Gradients
- No `bg-gradient-*` classes
- No CSS gradients in custom styles
- Reason: Reduces accessibility, complicates theming, increases maintenance

### ❌ Emojis
- No emojis in UI text or icons
- Use SVG icons or text-only labels
- Reason: Inconsistent rendering, accessibility issues, cultural differences

### ❌ Heavy Shadows
- No `shadow-xl`, `shadow-2xl`, or custom box-shadow
- Use `shadow-sm` or `shadow-md` only for subtle elevation
- Reason: Dark theme doesn't need heavy shadows, reduces visual noise

### ❌ Flashy Effects
- No animations except for state transitions (`transition-colors duration-200`)
- No hover effects beyond color changes
- No transforms, scales, or rotations
- Reason: Maintains focus on content, reduces motion sensitivity issues

### ❌ Custom Colors
- No arbitrary color values (e.g., `bg-[#123456]`)
- No custom CSS color variables beyond the defined palette
- Reason: Ensures consistency, simplifies maintenance

### ❌ Custom Spacing
- No arbitrary spacing values (e.g., `p-[17px]`)
- No custom CSS spacing variables
- Reason: Maintains design system consistency

## Implementation Guidelines

### Component Structure
- Use semantic HTML elements
- Apply design rules through Tailwind classes only
- Avoid inline styles
- Maintain consistent component APIs

### Responsive Design
- Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`)
- Mobile-first approach
- Test on multiple screen sizes

### Accessibility
- Maintain proper contrast ratios
- Use semantic color names for states
- Support keyboard navigation
- Provide focus indicators

## Enforcement
These rules are mandatory for all new frontend development. Existing code should be gradually migrated to comply with these constraints. Any deviations require explicit approval and documentation of the rationale.

## Review Process
- Design decisions must reference these rules
- Code reviews should check compliance
- New patterns require updating this document
