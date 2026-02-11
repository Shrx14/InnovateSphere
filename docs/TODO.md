# Fix Explore Page Token Clear Issue

## Steps
- [x] 1. Analyze codebase and identify root cause
- [x] 2. Fix AuthContext.jsx - JWT expiration check bug
- [x] 3. Fix AuthContext.jsx - Add auth:logout event listener
- [x] 4. Update ExplorePage.jsx - Add conditional rendering for auth users
- [x] 5. Update Header.jsx - Add auth-aware navigation
- [x] 6. Test the fixes



## Root Cause
The `hydrateUserFromToken` function in AuthContext.jsx has a floating-point comparison bug:
```javascript
payload.exp < Date.now() / 1000  // Date.now()/1000 returns float with milliseconds
```
This causes valid tokens to appear expired due to precision issues.

## Files to Edit
1. `frontend/src/context/AuthContext.jsx` - Fix token validation and add event listener
2. `frontend/src/features/explore/pages/ExplorePage.jsx` - Add auth context usage
3. `frontend/src/features/shared/layout/Header.jsx` - Add auth-aware navigation
