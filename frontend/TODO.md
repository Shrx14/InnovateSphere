# TODO: Fix Login Flow

## Step 1: Update Login Handler
- Modify handleSubmit in Login component to store JWT in localStorage
- Set user state to dummy object after successful login
- Remove the setTimeout for message, since we redirect

## Step 2: Add Route Guard
- Add useEffect in InnovateSphereAuth to check localStorage for token on mount
- If token present, set user to dummy object

## Step 3: Update Logout
- Modify handleLogout to remove token from localStorage

## Step 4: Update Protected API Calls
- Update NoveltyChecker to include Authorization header
- Update ProjectIdeas (generate-idea) to include Authorization header

## Step 5: Test
- Verify login stores token and shows dashboard
- Verify refresh keeps logged in
- Verify logout removes token
- Verify API calls work with token
