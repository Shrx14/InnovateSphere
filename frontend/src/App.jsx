import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminShell from "./features/admin/components/AdminShell";
import UserShell from "./features/user/components/UserShell";
import PublicShell from "./features/shared/components/PublicShell";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminProtectedRoute from "./components/AdminProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Toaster } from "./components/ui/Toaster";

/* Admin Pages */
import AdminReviewQueue from "./features/admin/pages/AdminReviewQueue";
import AdminIdeaDetail from "./features/admin/pages/AdminIdeaDetail";
import AdminAnalytics from "./features/admin/pages/AdminAnalytics";
import AdminAbuseEvents from "./features/admin/pages/AdminAbuseEvents";

/* User Pages */
import LandingPage from "./features/landing/pages/LandingPage";
import ExplorePage from "./features/explore/pages/ExplorePage";
import UserDashboard from "./features/dashboard/pages/UserDashboard";
import LoginPage from "./features/auth/pages/LoginPage";
import RegisterPage from "./features/auth/pages/RegisterPage";
import IdeaDetail from "./features/idea/pages/IdeaDetail";
import GeneratePage from "./features/generate/pages/GeneratePage";
import NoveltyPage from "./features/novelty/pages/NoveltyPage";
import MyIdeasPage from "./features/novelty/pages/MyIdeasPage";

const NotFoundPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-neutral-950 px-6">
    <div className="text-center max-w-md">
      <h1 className="text-7xl font-bold text-indigo-500 mb-4">404</h1>
      <h2 className="text-2xl font-light text-white mb-4">Page not found</h2>
      <p className="text-neutral-400 mb-8">The page you&apos;re looking for doesn&apos;t exist or has been moved.</p>
      <a href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-500 transition">
        Go Home
      </a>
    </div>
  </div>
);

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ErrorBoundary>
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
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </PublicShell>
          }
        />

        </Routes>
        <Toaster />
        </ErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
};


export default App;
