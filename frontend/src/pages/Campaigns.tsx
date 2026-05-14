import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCampaigns, createCampaign, deleteCampaign } from "../api/campaigns";
import { getTemplates } from "../api/template";
import type { Campaign } from "../types";

type Template = {
  id: number;
  name: string;
  category: string;
};

function Campaigns() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [tab, setTab] = useState<"active" | "completed">("active");
  const [selectedTemplateName, setSelectedTemplateName] = useState<string>("");

  const [form, setForm] = useState({
    name: "",
    event_date: "",
    end_date: "",
    location: "",
    distributor_name: "",
    description: "",
    followup_delay_1: 7,
    followup_delay_2: 14,
    followup_delay_3: 21,
    template_initial_id: undefined as number | undefined,
    template_followup_1_id: undefined as number | undefined,
    template_followup_2_id: undefined as number | undefined,
    template_followup_3_id: undefined as number | undefined,
  });

  useEffect(() => {
    fetchCampaigns();
    fetchTemplates();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await getCampaigns();
      setCampaigns(data);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch {
      // silently fail
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createCampaign({
      ...form,
      end_date: form.end_date || undefined,
      location: form.location || undefined,
      distributor_name: form.distributor_name || undefined,
      description: form.description || undefined,
    });
    setShowForm(false);
    setSelectedTemplateName("");
    setForm({
      name: "",
      event_date: "",
      end_date: "",
      location: "",
      distributor_name: "",
      description: "",
      followup_delay_1: 7,
      followup_delay_2: 14,
      followup_delay_3: 21,
      template_initial_id: undefined,
      template_followup_1_id: undefined,
      template_followup_2_id: undefined,
      template_followup_3_id: undefined,
    });
    fetchCampaigns();
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
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + New Campaign
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">New Campaign</h3>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Location
              </label>
              <input
                type="text"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Start Date *
              </label>
              <input
                type="date"
                value={form.event_date}
                onChange={(e) =>
                  setForm({ ...form, event_date: e.target.value })
                }
                className="w-full border rounded px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Distributor
              </label>
              <input
                type="text"
                value={form.distributor_name}
                onChange={(e) =>
                  setForm({ ...form, distributor_name: e.target.value })
                }
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Description
              </label>
              <input
                type="text"
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>

            {/* Follow-up delays */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Follow-up Delays (days)
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[1, 2, 3].map((n) => (
                  <div key={n}>
                    <label className="block text-sm text-gray-500 mb-1">
                      Follow-up {n}
                    </label>
                    <input
                      type="number"
                      value={form[`followup_delay_${n}` as keyof typeof form]}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          [`followup_delay_${n}`]: Number(e.target.value),
                        })
                      }
                      className="w-full border rounded px-3 py-2 text-sm"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Email templates */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📧 Email Templates{" "}
                <span className="text-gray-400 font-normal">
                  (optional — uses your default templates if not set)
                </span>
              </label>
              <select
                value={selectedTemplateName}
                onChange={(e) => {
                  const name = e.target.value;
                  setSelectedTemplateName(name);
                  if (!name) {
                    setForm({
                      ...form,
                      template_initial_id: undefined,
                      template_followup_1_id: undefined,
                      template_followup_2_id: undefined,
                      template_followup_3_id: undefined,
                    });
                    return;
                  }
                  const t_initial = templates.find(
                    (t) => t.name === name && t.category === "initial",
                  );
                  const t_f1 = templates.find(
                    (t) => t.name === name && t.category === "followup_1",
                  );
                  const t_f2 = templates.find(
                    (t) => t.name === name && t.category === "followup_2",
                  );
                  const t_f3 = templates.find(
                    (t) => t.name === name && t.category === "followup_3",
                  );
                  setForm({
                    ...form,
                    template_initial_id: t_initial?.id,
                    template_followup_1_id: t_f1?.id,
                    template_followup_2_id: t_f2?.id,
                    template_followup_3_id: t_f3?.id,
                  });
                }}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="">— Default templates —</option>
                {[...new Set(templates.map((t) => t.name))].map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-span-2 flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-sm text-gray-600 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </form>
        </div>
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
