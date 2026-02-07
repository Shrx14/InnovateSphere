# Frontend Reorganization Plan

## Current Structure Issues
1. Files scattered across: `admin/`, `app/admin/`, `app/auth/`, `user/`, `layouts/`, `shared/`, etc.
2. Admin files split between `admin/` and `app/admin/`
3. Unused file: `app/layout/AppShell.jsx` (not imported anywhere)
4. Inconsistent relative import paths

## Target Structure

```
frontend/src/
├── assets/              # Static assets (images, fonts)
├── components/          # Shared reusable UI components
│   └── ProtectedRoute.jsx
├── config/              # Configuration files
│   └── config.js
├── context/             # React contexts
│   └── AuthContext.jsx
├── features/            # Feature-based modules
│   ├── admin/           # All admin-related
│   │   ├── components/
│   │   │   ├── AdminNav.jsx
│   │   │   └── AdminShell.jsx
│   │   └── pages/
│   │       ├── AdminAnalytics.jsx
│   │       ├── AdminIdeaDetail.jsx
│   │       └── AdminReviewQueue.jsx
│   ├── auth/            # Authentication
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       └── RegisterPage.jsx
│   ├── dashboard/       # User dashboard
│   │   └── pages/
│   │       └── UserDashboard.jsx
│   ├── explore/         # Explore functionality
│   │   └── pages/
│   │       ├── ExploreAuthenticated.jsx
│   │       └── ExplorePage.jsx
│   ├── generate/        # Idea generation
│   │   └── pages/
│   │       ├── GenerateIdea.jsx
│   │       ├── GeneratePage.jsx
│   │       └── GenerateResult.jsx
│   ├── idea/            # Idea details
│   │   └── pages/
│   │       └── IdeaDetail.jsx
│   ├── landing/         # Landing page
│   │   └── pages/
│   │       └── LandingPage.jsx
│   ├── shared/          # Shared feature components
│   │   ├── components/
│   │   │   └── PublicShell.jsx
│   │   └── layout/
│   │       ├── Footer.jsx
│   │       └── Header.jsx
│   └── user/            # User-specific
│       └── components/
│           ├── UserNav.jsx
│           └── UserShell.jsx
├── hooks/               # Custom hooks
│   └── useDebounce.js
├── lib/                 # Utility libraries
│   ├── api.js           # (from shared/api.js)
│   └── motionTokens.js  # (from shared/motionTokens.js)
├── styles/              # Global styles
│   ├── App.css
│   └── index.css
├── utils/               # Utility functions (if needed)
├── App.jsx              # Main app entry
├── index.js             # Entry point
├── logo.svg
├── reportWebVitals.js
└── setupTests.js
```

## File Mapping (Source → Destination)

| Source | Destination |
|--------|-------------|
| `admin/AdminIdeaDetail.jsx` | `features/admin/pages/AdminIdeaDetail.jsx` |
| `admin/AdminReviewQueue.jsx` | `features/admin/pages/AdminReviewQueue.jsx` |
| `app/admin/AdminAnalytics.jsx` | `features/admin/pages/AdminAnalytics.jsx` |
| `app/admin/AdminNav.jsx` | `features/admin/components/AdminNav.jsx` |
| `app/auth/LoginPage.jsx` | `features/auth/pages/LoginPage.jsx` |
| `app/auth/RegisterPage.jsx` | `features/auth/pages/RegisterPage.jsx` |
| `app/dashboard/UserDashboard.jsx` | `features/dashboard/pages/UserDashboard.jsx` |
| `app/explore/ExplorePage.jsx` | `features/explore/pages/ExplorePage.jsx` |
| `app/explore/ExploreAuthenticated.jsx` | `features/explore/pages/ExploreAuthenticated.jsx` |
| `app/generate/GeneratePage.jsx` | `features/generate/pages/GeneratePage.jsx` |
| `app/generate/GenerateIdea.jsx` | `features/generate/pages/GenerateIdea.jsx` |
| `app/generate/GenerateResult.jsx` | `features/generate/pages/GenerateResult.jsx` |
| `app/idea/IdeaDetail.jsx` | `features/idea/pages/IdeaDetail.jsx` |
| `app/landing/LandingPage.jsx` | `features/landing/pages/LandingPage.jsx` |
| `app/layout/AppShell.jsx` | **DELETE** (unused) |
| `components/ProtectedRoute.jsx` | `components/ProtectedRoute.jsx` (keep) |
| `config.js` | `config/config.js` |
| `context/AuthContext.jsx` | `context/AuthContext.jsx` (keep) |
| `hooks/useDebounce.js` | `hooks/useDebounce.js` (keep) |
| `layouts/AdminShell.jsx` | `features/admin/components/AdminShell.jsx` |
| `layouts/PublicShell.jsx` | `features/shared/components/PublicShell.jsx` |
| `layouts/UserShell.jsx` | `features/user/components/UserShell.jsx` |
| `shared/api.js` | `lib/api.js` |
| `shared/motionTokens.js` | `lib/motionTokens.js` |
| `shared/layout/Footer.jsx` | `features/shared/layout/Footer.jsx` |
| `shared/layout/Header.jsx` | `features/shared/layout/Header.jsx` |
| `user/UserNav.jsx` | `features/user/components/UserNav.jsx` |

## Import Path Updates Required

### App.jsx
```javascript
// Admin imports
import AdminShell from "./features/admin/components/AdminShell";
import AdminReviewQueue from "./features/admin/pages/AdminReviewQueue";
import AdminIdeaDetail from "./features/admin/pages/AdminIdeaDetail";
import AdminAnalytics from "./features/admin/pages/AdminAnalytics";

// User imports  
import UserShell from "./features/user/components/UserShell";
import UserDashboard from "./features/dashboard/pages/UserDashboard";
import GeneratePage from "./features/generate/pages/GeneratePage";

// Public imports
import PublicShell from "./features/shared/components/PublicShell";
import LandingPage from "./features/landing/pages/LandingPage";
import ExplorePage from "./features/explore/pages/ExplorePage";
import LoginPage from "./features/auth/pages/LoginPage";
import RegisterPage from "./features/auth/pages/RegisterPage";
import IdeaDetail from "./features/idea/pages/IdeaDetail";
```

### AdminShell.jsx
```javascript
import AdminNav from "./AdminNav";
```

### UserShell.jsx
```javascript
import UserNav from "./UserNav";
```

### PublicShell.jsx
```javascript
import Header from "../layout/Header";
```

### Page files with API imports
```javascript
// Change from:
import api from '../../shared/api';
// To:
import api from '../../../lib/api';
```

### Page files with AuthContext imports
```javascript
// Change from:
import { useAuth } from '../../context/AuthContext';
// To:
import { useAuth } from '../../../context/AuthContext';
```

## Directories to Remove After Migration
- `admin/`
- `app/` (entire directory)
- `layouts/`
- `shared/`
- `user/`

## Execution Checklist

### Phase 1: Create Directory Structure
- [ ] Create `features/admin/components/`
- [ ] Create `features/admin/pages/`
- [ ] Create `features/auth/pages/`
- [ ] Create `features/dashboard/pages/`
- [ ] Create `features/explore/pages/`
- [ ] Create `features/generate/pages/`
- [ ] Create `features/idea/pages/`
- [ ] Create `features/landing/pages/`
- [ ] Create `features/shared/components/`
- [ ] Create `features/shared/layout/`
- [ ] Create `features/user/components/`
- [ ] Create `lib/`
- [ ] Create `config/`

### Phase 2: Move Files
- [ ] Move all admin files
- [ ] Move all auth files
- [ ] Move all dashboard files
- [ ] Move all explore files
- [ ] Move all generate files
- [ ] Move all idea files
- [ ] Move all landing files
- [ ] Move all shared layout files
- [ ] Move all user files
- [ ] Move api.js and motionTokens.js to lib/
- [ ] Move config.js to config/

### Phase 3: Update Imports
- [ ] Update App.jsx
- [ ] Update AdminShell.jsx
- [ ] Update UserShell.jsx
- [ ] Update PublicShell.jsx
- [ ] Update all page files with API imports
- [ ] Update all page files with context imports
- [ ] Update all page files with hook imports

### Phase 4: Cleanup
- [ ] Delete `admin/` directory
- [ ] Delete `app/` directory
- [ ] Delete `layouts/` directory
- [ ] Delete `shared/` directory
- [ ] Delete `user/` directory
- [ ] Delete root `config.js` if exists

### Phase 5: Verification
- [ ] Verify all imports resolve
- [ ] Check for any broken paths
- [ ] Test application routes
