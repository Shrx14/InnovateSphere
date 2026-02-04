import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminShell from "./layouts/AdminShell";
import UserShell from "./layouts/UserShell";

/* Admin Pages */
import AdminReviewQueue from "./admin/AdminReviewQueue";

/* User Pages */
import LandingPage from "./app/landing/LandingPage";
import ExplorePage from "./app/explore/ExplorePage";
import UserDashboard from "./app/dashboard/UserDashboard";

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
                <Route path="review" element={<AdminReviewQueue />} />
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
                <Route path="dashboard" element={<UserDashboard />} />
              </Routes>
            </UserShell>
          }
        />

      </Routes>
    </BrowserRouter>
  );
};

export default App;
