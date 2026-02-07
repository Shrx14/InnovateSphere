# Remove Framer Motion from User UI

## Step 1: Remove Framer Motion usage
- [ ] Edit frontend/src/app/landing/LandingPage.jsx: Remove motion import, replace motion.section with section in HeroStatBlock and TopIdeasPreview
- [ ] Edit frontend/src/app/generate/GenerateResult.jsx: Remove motion import, replace motion.section with section
- [ ] Edit frontend/src/app/dashboard/UserDashboard.jsx: Remove motion import, replace motion.div with div
- [ ] Edit frontend/src/app/explore/ExplorePage.jsx: Remove motion import, replace motion.main with main and motion.div with div

## Step 2: Uninstall Framer Motion
- [ ] Run npm uninstall framer-motion in frontend directory

## Step 3: Restart clean
- [ ] rm -rf node_modules package-lock.json
- [ ] npm install
- [ ] npm start
