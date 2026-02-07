import { Link } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";

const UserNav = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="border-b border-neutral-800">
      <div className="px-6 py-4 max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/" className="text-lg font-medium text-white">
          InnovateSphere
        </Link>

        <nav className="flex gap-6 text-sm">
          <Link to="/explore" className="text-neutral-300 hover:text-white">
            Explore
          </Link>
          {isAuthenticated ? (
            <>
              <Link to="/generate" className="text-neutral-300 hover:text-white">
                Generate
              </Link>
              <Link to="/dashboard" className="text-neutral-300 hover:text-white">
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="text-neutral-300 hover:text-white"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-neutral-300 hover:text-white">
                Login
              </Link>
              <Link to="/register" className="text-neutral-300 hover:text-white">
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

export default UserNav;
