import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import AppShell from './app/layout/AppShell';
import LandingPage from './app/landing/LandingPage';
import IdeaDetail from './app/idea/IdeaDetail';
import ReviewQueue from './app/admin/ReviewQueue';
import ExplorePage from './app/explore/ExplorePage';
import ExploreAuthenticated from './app/explore/ExploreAuthenticated';
import LoginPage from './app/auth/LoginPage';
import RegisterPage from './app/auth/RegisterPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/explore/advanced" element={
            <ProtectedRoute>
              <ExploreAuthenticated />
            </ProtectedRoute>
          } />
          <Route path="/idea/:id" element={<IdeaDetail />} />
          <Route path="/admin/review" element={
            <ProtectedRoute role="admin">
              <ReviewQueue />
            </ProtectedRoute>
          } />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </AppShell>
    </Router>
  );
}

export default App;
