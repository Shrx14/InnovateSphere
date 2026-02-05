import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminShell from "./layouts/AdminShell";
import UserShell from "./layouts/UserShell";

/* Admin Pages */
import AdminReviewQueue from "./admin/AdminReviewQueue";
import AdminIdeaDetail from "./admin/AdminIdeaDetail";

/* User Pages */
import LandingPage from "./app/landing/LandingPage";
import ExplorePage from "./app/explore/ExplorePage";
import UserDashboard from "./app/dashboard/UserDashboard";
import LoginPage from "./app/auth/LoginPage";
import RegisterPage from "./app/auth/RegisterPage";
import IdeaDetail from "./app/idea/IdeaDetail";
import GeneratePage from "./app/generate/GeneratePage";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>

        {/* ================= ADMIN ROUTES ================= */}
        <Route
          path="/admin/*"
          element={
            <AdminShell>
              <Routes>
                <Route path="/" element={<AdminReviewQueue />} />
                <Route path="review" element={<AdminReviewQueue />} />
                <Route path="idea/:id" element={<AdminIdeaDetail />} />
              </Routes>
            </AdminShell>
          }
        />

        {/* ================= USER ROUTES ================= */}
        <Route
          path="/*"
          element={
            <UserShell>
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="explore" element={<ExplorePage />} />
                <Route path="idea/:id" element={<IdeaDetail />} />
                <Route path="login" element={<LoginPage />} />
                <Route path="register" element={<RegisterPage />} />
                <Route path="dashboard" element={<UserDashboard />} />
                <Route path="generate" element={<GeneratePage />} />
              </Routes>
            </UserShell>
          }
        />

      </Routes>
    </BrowserRouter>
  );
};

export default App;
