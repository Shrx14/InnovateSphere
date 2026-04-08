import { useEffect, useState } from "react";
import AdminNav from "./AdminNav";
import api from "../../../lib/api";

const AdminShell = ({ children }) => {
  const [pipelineVersion, setPipelineVersion] = useState(null);

  useEffect(() => {
    api.get("/ai/pipeline-version")
      .then(res => setPipelineVersion(res.data.version))
      .catch(() => setPipelineVersion(null));
  }, []);

  return (
    <div className="min-h-screen text-neutral-200" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <AdminNav />

      <main className="px-6 py-6 max-w-7xl mx-auto">
        {children}
      </main>

      {pipelineVersion && (
        <footer className="border-t border-neutral-800 py-3 px-6">
          <div className="max-w-7xl mx-auto flex justify-end">
            <span className="text-xs text-neutral-500">
              Pipeline <span className="text-neutral-400 font-mono">{pipelineVersion}</span>
            </span>
          </div>
        </footer>
      )}
    </div>
  );
};

export default AdminShell;
