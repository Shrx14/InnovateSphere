import { Link } from "react-router-dom";

const UserNav = () => {
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
          <Link to="/dashboard" className="text-neutral-300 hover:text-white">
            Dashboard
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default UserNav;
