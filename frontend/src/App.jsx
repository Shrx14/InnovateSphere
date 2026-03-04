import React, { Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminShell from "./features/admin/components/AdminShell";
import UserShell from "./features/user/components/UserShell";
import PublicShell from "./features/shared/components/PublicShell";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminProtectedRoute from "./components/AdminProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Toaster } from "./components/ui/Toaster";
import CustomCursor from "./components/CustomCursor";

/* Route-level code splitting with React.lazy */
const AdminReviewQueue = React.lazy(() => import("./features/admin/pages/AdminReviewQueue"));
const AdminIdeaDetail = React.lazy(() => import("./features/admin/pages/AdminIdeaDetail"));
const AdminAnalytics = React.lazy(() => import("./features/admin/pages/AdminAnalytics"));
const AdminAbuseEvents = React.lazy(() => import("./features/admin/pages/AdminAbuseEvents"));
const LandingPage = React.lazy(() => import("./features/landing/pages/LandingPage"));
const ExplorePage = React.lazy(() => import("./features/explore/pages/ExplorePage"));
const UserDashboard = React.lazy(() => import("./features/dashboard/pages/UserDashboard"));
const LoginPage = React.lazy(() => import("./features/auth/pages/LoginPage"));
const RegisterPage = React.lazy(() => import("./features/auth/pages/RegisterPage"));
const IdeaDetail = React.lazy(() => import("./features/idea/pages/IdeaDetail"));
const GeneratePage = React.lazy(() => import("./features/generate/pages/GeneratePage"));
const NoveltyPage = React.lazy(() => import("./features/novelty/pages/NoveltyPage"));
const MyIdeasPage = React.lazy(() => import("./features/novelty/pages/MyIdeasPage"));
const AboutPage = React.lazy(() => import("./features/static/pages/AboutPage"));
const ContactPage = React.lazy(() => import("./features/static/pages/ContactPage"));
const PrivacyPage = React.lazy(() => import("./features/static/pages/PrivacyPage"));
const TermsPage = React.lazy(() => import("./features/static/pages/TermsPage"));
const HowItWorksPage = React.lazy(() => import("./features/static/pages/HowItWorksPage"));

const RouteFallback = () => (
  <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
    <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
  </div>
);

const NotFoundPage = () => (
  <div className="min-h-screen flex items-center justify-center px-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
    <div className="text-center max-w-md">
      <h1 className="text-7xl font-bold text-indigo-500 mb-4">404</h1>
      <h2 className="text-2xl font-light mb-4" style={{ color: 'var(--text-primary)' }}>Page not found</h2>
      <p className="dark:text-neutral-400 text-neutral-500 dark:text-neutral-400 mb-8">The page you&apos;re looking for doesn&apos;t exist or has been moved.</p>
      <a href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-500 transition">
        Go Home
      </a>
    </div>
  </div>
);


const App = () => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <CustomCursor />
            <Suspense fallback={<RouteFallback />}>
              <Routes>


                {/* ================= ADMIN ROUTES ================= */}
                <Route
                  path="/admin/*"
                  element={
                    <AdminProtectedRoute>
                      <AdminShell>
                        <Routes>
                          <Route path="/" element={<AdminReviewQueue />} />
                          <Route path="review" element={<AdminReviewQueue />} />
                          <Route path="analytics" element={<AdminAnalytics />} />
                          <Route path="abuse" element={<AdminAbuseEvents />} />
                          <Route path="idea/:id" element={<AdminIdeaDetail />} />
                        </Routes>
                      </AdminShell>
                    </AdminProtectedRoute>
                  }
                />

                {/* ================= USER ROUTES ================= */}
                <Route
                  path="/user/*"
                  element={
                    <UserShell>
                      <Routes>
                        <Route path="dashboard" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
                        <Route path="generate" element={<ProtectedRoute><GeneratePage /></ProtectedRoute>} />
                        <Route path="novelty" element={<ProtectedRoute><NoveltyPage /></ProtectedRoute>} />
                        <Route path="my-ideas" element={<ProtectedRoute><MyIdeasPage /></ProtectedRoute>} />
                      </Routes>
                    </UserShell>
                  }
                />

                {/* ================= PUBLIC ROUTES (catch-all, must be last) ================= */}
                <Route
                  path="/*"
                  element={
                    <PublicShell>
                      <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="explore" element={<ExplorePage />} />
                        <Route path="idea/:id" element={<IdeaDetail />} />
                        <Route path="login" element={<LoginPage />} />
                        <Route path="register" element={<RegisterPage />} />
                        <Route path="about" element={<AboutPage />} />
                        <Route path="contact" element={<ContactPage />} />
                        <Route path="privacy" element={<PrivacyPage />} />
                        <Route path="terms" element={<TermsPage />} />
                        <Route path="how-it-works" element={<HowItWorksPage />} />
                        <Route path="*" element={<NotFoundPage />} />
                      </Routes>
                    </PublicShell>
                  }
                />

              </Routes>
            </Suspense>
            <Toaster />
          </ErrorBoundary>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};


export default App;
