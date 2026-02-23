import AdminNav from "./AdminNav";
import StarfieldBackground from "@/components/StarfieldBackground";

const AdminShell = ({ children }) => {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-200 relative">
      <StarfieldBackground />
      <div className="relative z-10">
        <AdminNav />
        <main className="px-6 py-6 max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminShell;
