import { useEffect, useState } from "react";
import api from "../../../lib/api";

export default function UserDashboard() {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/ideas/mine")
      .then(res => setIdeas(res.data.ideas))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-gray-400">Loading ideas…</p>;
  }

  if (ideas.length === 0) {
    return <p className="text-sm text-gray-400">No ideas generated yet.</p>;
  }

  const grouped = {
    validated: ideas.filter(i => i.status === "validated"),
    pending: ideas.filter(i => i.status === "pending"),
    rejected: ideas.filter(i => i.status === "rejected" || i.status === "downgraded"),
  };

  const renderSection = (title, ideasList) => (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wide">
        {title}
      </h3>
      <div className="space-y-4">
        
        {ideasList.map(idea => (
          <div
            key={idea.id}
            className={`border rounded-lg p-6 bg-gray-900 ${
              idea.status === "validated"
                ? "border-emerald-700/40 bg-emerald-950/20"
                : "border-gray-800"
            }`}
          >
            <div className="flex justify-between">
              <h2 className="text-lg text-white font-medium">
                {idea.title}
              </h2>
              <span className={`text-xs ${
                idea.status === "validated"
                  ? "text-emerald-400"
                  : idea.status === "pending"
                  ? "text-yellow-400"
                  : "text-red-400"
              }`}>
                {idea.status}
              </span>
            </div>

            <div className="mt-2 text-sm text-gray-400">
              Domain: {idea.domain}
            </div>

            <div className="mt-3 flex gap-6 text-sm">
              <span>Novelty: {idea.novelty_score}</span>
              <span>Quality: {idea.quality_score}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      {grouped.validated.length > 0 && renderSection("Validated", grouped.validated)}
      {grouped.pending.length > 0 && renderSection("Pending", grouped.pending)}
      {grouped.rejected.length > 0 && renderSection("Rejected", grouped.rejected)}
    </div>
  );
}
