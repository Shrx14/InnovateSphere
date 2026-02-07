import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminShell from "./features/admin/components/AdminShell";
import UserShell from "./features/user/components/UserShell";
import PublicShell from "./features/shared/components/PublicShell";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";


/* Admin Pages */
import AdminReviewQueue from "./features/admin/pages/AdminReviewQueue";
import AdminIdeaDetail from "./features/admin/pages/AdminIdeaDetail";
import AdminAnalytics from "./features/admin/pages/AdminAnalytics";

/* User Pages */
import LandingPage from "./features/landing/pages/LandingPage";
import ExplorePage from "./features/explore/pages/ExplorePage";
import UserDashboard from "./features/dashboard/pages/UserDashboard";
import LoginPage from "./features/auth/pages/LoginPage";
import RegisterPage from "./features/auth/pages/RegisterPage";
import IdeaDetail from "./features/idea/pages/IdeaDetail";
import GeneratePage from "./features/generate/pages/GeneratePage";


const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>


        {/* ================= ADMIN ROUTES ================= */}
        <Route
          path="/admin/*"
          element={
            <AdminShell>
              <Routes>
                <Route path="/" element={<AdminReviewQueue />} />
                <Route path="review" element={<AdminReviewQueue />} />
                <Route path="analytics" element={<AdminAnalytics />} />
                <Route path="idea/:id" element={<AdminIdeaDetail />} />
              </Routes>
            </AdminShell>
          }
        />

        {/* ================= PUBLIC ROUTES ================= */}
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
              </Routes>
            </PublicShell>
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
              </Routes>
            </UserShell>
          }
        />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};


export default App;
