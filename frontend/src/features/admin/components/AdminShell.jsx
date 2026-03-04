import AdminNav from "./AdminNav";

const AdminShell = ({ children }) => {
  return (
    <div className="min-h-screen dark:text-neutral-200 text-neutral-700" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <AdminNav />

      <main className="px-6 py-6 max-w-7xl mx-auto">
        {children}
      </main>
    </div>
  );
};

export default AdminShell;
