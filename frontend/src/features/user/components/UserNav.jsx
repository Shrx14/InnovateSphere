import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";
import { cn } from "@/lib/utils";

const navLinkClass = ({ isActive }) =>
  cn(
    "text-sm transition-colors",
    isActive ? "text-white font-medium" : "text-neutral-400 hover:text-white"
  );

const UserNav = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-neutral-950/80 backdrop-blur-lg border-b border-neutral-800/60">
      <div className="px-6 py-4 max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/" className="text-lg font-medium text-white">
          InnovateSphere
        </Link>

        <nav className="flex items-center gap-6 text-sm">
          <NavLink to="/explore" className={navLinkClass}>
            Explore
          </NavLink>
          {isAuthenticated ? (
            <>
              <NavLink to="/user/dashboard" className={navLinkClass}>
                Dashboard
              </NavLink>
              <NavLink to="/user/generate" className={navLinkClass}>
                Generate
              </NavLink>
              <NavLink to="/user/novelty" className={navLinkClass}>
                Novelty
              </NavLink>
              <button
                onClick={logout}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navLinkClass}>
                Login
              </NavLink>
              <NavLink to="/register" className={navLinkClass}>
                Register
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

export default UserNav;
