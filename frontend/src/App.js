import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import AppShell from './app/layout/AppShell';
import LandingPage from './app/landing/LandingPage';
import IdeaDetail from './app/idea/IdeaDetail';
import ReviewQueue from './app/admin/ReviewQueue';
import ExplorePage from './app/explore/ExplorePage';

function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/idea/:id" element={<IdeaDetail />} />
          <Route path="/admin/review" element={<ReviewQueue />} />
          <Route path="/explore" element={<ExplorePage />} />
        </Routes>
      </AppShell>
    </Router>
  );
}

export default App;
