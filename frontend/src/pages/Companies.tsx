import React, { useEffect, useState } from "react";
import { getCompanies, createCompany, deleteCompany } from "../api/companies";
import type { Company } from "../types";

function Companies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");

  const [form, setForm] = useState({
    name: "",
    market: "",
    website: "",
    notes: "",
    chain_level: "",
    end_user_type: "",
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const data = await getCompanies();
      setCompanies(data);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createCompany({
      name: form.name,
      market: form.market || undefined,
      website: form.website || undefined,
      notes: form.notes || undefined,
      chain_level: (form.chain_level || undefined) as Company["chain_level"],
      // end_user_type only sent when chain_level = end_user
      end_user_type:
        form.chain_level === "end_user"
          ? ((form.end_user_type || undefined) as Company["end_user_type"])
          : undefined,
    });
    setShowForm(false);
    setForm({
      name: "",
      market: "",
      website: "",
      notes: "",
      chain_level: "",
      end_user_type: "",
    });
    fetchCompanies();
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete ${name}?`)) return;
    await deleteCompany(id);
    fetchCompanies();
  };

  const filtered = companies.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.market ?? "").toLowerCase().includes(search.toLowerCase()),
  );

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Companies</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + New Company
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">
            Create New Company
          </h3>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full border border-gray-300 rounded-md p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Market</label>
              <input
                type="text"
                value={form.market}
                onChange={(e) => setForm({ ...form, market: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Website
              </label>
              <input
                type="text"
                value={form.website}
                onChange={(e) => setForm({ ...form, website: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              {/* Chain Level = position dans la chaîne de distribution (niveau 1) */}
              <label className="block text-sm text-gray-600 mb-1">
                Chain Level *
              </label>
              <select
                value={form.chain_level}
                onChange={(e) =>
                  setForm({
                    ...form,
                    chain_level: e.target.value,
                    end_user_type: "",
                  })
                }
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="">Select position...</option>
                <option value="distributor">🏭 Distributor</option>
                <option value="importer">🚢 Importer</option>
                <option value="broker">🤝 Broker</option>
                <option value="end_user">🍽 End User</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* End User Type = sous-qualification, visible uniquement si chain_level = end_user */}
            {form.chain_level === "end_user" && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  End User Type
                </label>
                <select
                  value={form.end_user_type}
                  onChange={(e) =>
                    setForm({ ...form, end_user_type: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                >
                  <option value="">Select type...</option>
                  <option value="restaurant">🍴 Restaurant</option>
                  <option value="hotel">🏨 Hotel</option>
                  <option value="franchise">🔗 Franchise</option>
                  <option value="country_club">⛳ Country Club</option>
                  <option value="catering">🎉 Catering</option>
                  <option value="retail">🛒 Retail</option>
                  <option value="institutional">🏛 Institutional</option>
                  <option value="other">Other</option>
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-600 mb-1">Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="col-span-2 flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 rounded-md border text-sm hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <input
        type="text"
        placeholder="Search by name or market..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full border border-gray-300 rounded-md p-2 text-sm"
      />

      {/* Companies List */}
      {filtered.length === 0 ? (
        <p className="text-gray-400 text-sm">No companies found.</p>
      ) : (
        <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Market</th>
                <th className="px-4 py-2">Chain Level</th>
                <th className="px-4 py-2">End User Type</th>
                <th className="px-4 py-2">Website</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b">
                  <td className="px-4 py-2 font-medium">{c.name}</td>
                  <td className="px-4 py-2 text-gray-500">{c.market || "-"}</td>
                  <td className="px-4 py-2">
                    {c.chain_level ? (
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          c.chain_level === "distributor"
                            ? "bg-blue-100 text-blue-700"
                            : c.chain_level === "importer"
                              ? "bg-purple-100 text-purple-700"
                              : c.chain_level === "broker"
                                ? "bg-yellow-100 text-yellow-700"
                                : c.chain_level === "end_user"
                                  ? "bg-green-100 text-green-700"
                                  : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {c.chain_level.replace("_", " ")}
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    {c.end_user_type ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-600">
                        {c.end_user_type.replace("_", " ")}
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-gray-400 text-xs">
                    {c.website || "-"}
                  </td>
                  <td className="px-4 py-2">
                    <button
                      onClick={() => handleDelete(c.id, c.name)}
                      className="text-red-400 hover:text-red-600"
                    >
                      🗑 Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Companies;
