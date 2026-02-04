import { Link } from "react-router-dom";

const AdminNav = () => {
  return (
    <header className="border-b border-gray-800">
      <div className="px-6 py-4 max-w-7xl mx-auto flex gap-6 text-sm">
        <Link to="/admin/review" className="text-gray-300 hover:text-white">
          Review Queue
        </Link>
        <Link to="/admin/domains" className="text-gray-300 hover:text-white">
          Domains
        </Link>
      </div>
    </header>
  );
};

export default AdminNav;
