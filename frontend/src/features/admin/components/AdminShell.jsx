import AdminNav from "./AdminNav";

const AdminShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-200">
      <AdminNav />

      <main className="px-6 py-6 max-w-7xl mx-auto">
        {children}
      </main>
    </div>
  );
};

export default AdminShell;
