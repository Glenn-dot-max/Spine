import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCampaigns, deleteCampaign } from "../api/campaigns";
import type { Campaign } from "../types";
import CreateCampaignWizard from "../components/CreateCampaignWizard";

function Campaigns() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [tab, setTab] = useState<"active" | "completed">("active");

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await getCampaigns();
      setCampaigns(data);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this campaign?")) return;
    await deleteCampaign(id);
    fetchCampaigns();
  };

  const activeCampaigns = campaigns.filter((c) => c.status !== "completed");
  const completedCampaigns = campaigns.filter((c) => c.status === "completed");
  const displayed = tab === "active" ? activeCampaigns : completedCampaigns;

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Campaigns</h2>
        <button
          onClick={() => setShowWizard(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + New Campaign
        </button>
      </div>

      {/* Wizard modal */}
      {showWizard && (
        <CreateCampaignWizard
          onClose={() => {
            setShowWizard(false);
            fetchCampaigns();
          }}
        />
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setTab("active")}
          className={`px-4 py-2 text-sm font-medium ${tab === "active" ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500 hover:text-gray-700"}`}
        >
          Active ({activeCampaigns.length})
        </button>
        <button
          onClick={() => setTab("completed")}
          className={`px-4 py-2 text-sm font-medium ${tab === "completed" ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500 hover:text-gray-700"}`}
        >
          Completed ({completedCampaigns.length})
        </button>
      </div>

      {/* Campaign list */}
      {displayed.length === 0 ? (
        <p className="text-gray-400 text-sm">No campaigns yet</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayed.map((c) => (
            <div
              key={c.id}
              className="bg-white border rounded-lg p-5 shadow-sm hover:shadow-md transition"
            >
              <div className="flex justify-between items-start mb-2">
                <h3
                  onClick={() => navigate(`/campaigns/${c.id}`)}
                  className="font-semibold text-gray-800 cursor-pointer hover:text-blue-600"
                >
                  {c.name}
                </h3>
                <StatusBadge status={c.status} />
              </div>
              <p className="text-sm text-gray-500 mb-1">
                📍 {c.location || "—"}
              </p>
              <p className="text-sm text-gray-500 mb-3">📅 {c.event_date}</p>
              <div className="flex justify-between text-sm text-gray-500 mb-4">
                <span>👥 {c.contact_count} contacts</span>
                <span>📦 {c.product_count} products</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate(`/campaigns/${c.id}`)}
                  className="flex-1 text-sm bg-blue-50 text-blue-600 py-1 rounded hover:bg-blue-100"
                >
                  Open
                </button>
                <button
                  onClick={() => handleDelete(c.id)}
                  className="text-sm text-red-400 hover:text-red-600 px-2"
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    upcoming: "bg-yellow-100 text-yellow-700",
    completed: "bg-gray-100 text-gray-600",
  };
  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] ?? "bg-gray-100"}`}
    >
      {status}
    </span>
  );
}

export default Campaigns;
