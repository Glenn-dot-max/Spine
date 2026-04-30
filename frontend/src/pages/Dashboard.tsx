import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMe } from "../api/auth";
import { getCampaigns } from "../api/campaigns";
import { getProspects } from "../api/prospects";
import type { User, Campaign, Prospect } from "../types";

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userData, campaignsData, prospectsData] = await Promise.all([
          getMe(),
          getCampaigns(),
          getProspects(),
        ]);
        setUser(userData);
        setCampaigns(campaignsData);
        setProspects(prospectsData);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;

  const activeCampaigns = campaigns.filter((c) => c.status === "active");
  const upcomingCampaigns = campaigns.filter((c) => c.status === "upcoming");

  return (
    <div className="space-y-6">

      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800">
          Hello {user?.first_name} 👋
        </h2>
        <p className="text-gray-500 text-sm">Here is a summary of your activity</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Active Campaigns" value={activeCampaigns.length} color="blue" />
        <StatCard label="Upcoming Campaigns" value={upcomingCampaigns.length} color="yellow" />
        <StatCard label="Total Prospects" value={prospects.length} color="green" />
        <StatCard label="Total Campaigns" value={campaigns.length} color="gray" />
      </div>

      {/* Recent Campaigns */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-gray-800">Recent Campaigns</h3>
          <button
            onClick={() => navigate("/campaigns")}
            className="text-sm text-blue-600 hover:underline"
          >
            View all →
          </button>
        </div>

        {campaigns.length === 0 ? (
          <p className="text-gray-400 text-sm">No campaigns yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Name</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Contacts</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.slice(0, 5).map((c) => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/campaigns/${c.id}`)}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                >
                  <td className="py-2 font-medium">{c.name}</td>
                  <td className="py-2">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="py-2">{c.contact_count}</td>
                  <td className="py-2 text-gray-500">{c.event_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700",
    yellow: "bg-yellow-50 text-yellow-700",
    green: "bg-green-50 text-green-700",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <div className={`rounded-lg p-4 ${colors[color]}`}>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-sm mt-1">{label}</p>
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
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] ?? "bg-gray-100"}`}>
      {status}
    </span>
  );
}

export default Dashboard;