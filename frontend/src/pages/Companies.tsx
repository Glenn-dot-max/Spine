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
    type_structure: "",
    type_contact: "",
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
    await createCompany(form);
    setShowForm(false);
    setForm({
      name: "",
      market: "",
      website: "",
      notes: "",
      type_structure: "",
      type_contact: "",
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
              <label className="block text-sm text-gray-600 mb-1">
                Type Structure
              </label>
              <select
                value={form.type_structure}
                onChange={(e) =>
                  setForm({ ...form, type_structure: e.target.value })
                }
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="">Select</option>
                <option value="Retail">Retail</option>
                <option value="Foodservice">Foodservice</option>
                <option value="Industry">Industry</option>
                <option value="Distribution">Distribution</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Type Contact
              </label>
              <select
                value={form.type_contact}
                onChange={(e) =>
                  setForm({ ...form, type_contact: e.target.value })
                }
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="">Select</option>
                <option value="distributor">Distributor</option>
                <option value="restaurant">Restaurant</option>
                <option value="factory">Factory</option>
                <option value="consultant">Consultant</option>
                <option value="retailer">Retailer</option>
                <option value="other">Other</option>
              </select>
            </div>
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
                <th className="px-4 py-2">Type Structure</th>
                <th className="px-4 py-2">Type Contact</th>
                <th className="px-4 py-2">Website</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b">
                  <td className="px-4 py-2">{c.name}</td>
                  <td className="px-4 py-2">{c.market || "-"}</td>
                  <td className="px-4 py-2">{c.type_structure || "-"}</td>
                  <td className="px-4 py-2">{c.type_contact || "-"}</td>
                  <td className="px-4 py-2">{c.website || "-"}</td>
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
