import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getCampaign,
  getCampaignContacts,
  addContactToCampaign,
  sendInitialEmails,
  getScheduleFollowups,
  sendDueFollowups,
} from "../api/campaigns";
import { getProspects } from "../api/prospects";
import api from "../api/client";
import type { Campaign, CampaignContact, Prospect } from "../types";

function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const campaignId = Number(id);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [contacts, setContacts] = useState<CampaignContact[]>([]);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [followups, setFollowups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProspectId, setSelectedProspectId] = useState<number | "">("");
  const [sendingAll, setSendingAll] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    fetchAll();
  }, [campaignId]);

  const fetchAll = async () => {
    try {
      const [camp, ctcts, prosps, fups] = await Promise.all([
        getCampaign(campaignId),
        getCampaignContacts(campaignId),
        getProspects(),
        getScheduleFollowups(campaignId),
      ]);
      setCampaign(camp);
      setContacts(ctcts);
      setProspects(prosps);
      setFollowups(fups);
    } finally {
      setLoading(false);
    }
  };

  const handleAddContact = async () => {
    if (!selectedProspectId) return;
    try {
      await addContactToCampaign(campaignId, Number(selectedProspectId));
      setSelectedProspectId("");
      showMessage("success", "Contact added successfully");
      fetchAll();
    } catch {
      showMessage("error", "Contact already in campaign or error occurred");
    }
  };

  const handleSendInitial = async () => {
    if (!confirm("Send initial emails to all pending contacts?")) return;
    setSendingAll(true);
    try {
      await sendInitialEmails(campaignId);
      showMessage("success", "Emails sent successfully");
      fetchAll();
    } catch {
      showMessage("error", "Failed to send emails");
    } finally {
      setSendingAll(false);
    }
  };

  const handleSendSingle = async (prospectId: number) => {
    try {
      await api.post(
        `/api/campaigns/${campaignId}/contacts/${prospectId}/emails/send`,
      );
      showMessage("success", "Email sent");
      fetchAll();
    } catch {
      showMessage("error", "Failed to send email");
    }
  };

  const handleSendDueFollowups = async () => {
    try {
      await sendDueFollowups();
      showMessage("success", "Due follow-ups sent");
      fetchAll();
    } catch {
      showMessage("error", "Failed to send follow-ups");
    }
  };

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!campaign) return <p className="text-gray-500">Campaign not found</p>;

  // Prospects not yet in campaign
  const contactIds = contacts.map((c) => c.prospect_id);
  const availableProspects = prospects.filter(
    (p) => !contactIds.includes(p.id),
  );

  return (
    <div className="space-y-6">
      {/* Message */}
      {message && (
        <div
          className={`px-4 py-3 rounded text-sm ${message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
        >
          {message.text}
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">{campaign.name}</h2>
          <p className="text-gray-500 text-sm mt-1">
            📍 {campaign.location || "—"} &nbsp;|&nbsp; 📅 {campaign.event_date}
            {campaign.end_date && ` → ${campaign.end_date}`}
          </p>
        </div>
        <StatusBadge status={campaign.status} />
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleSendInitial}
          disabled={sendingAll}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {sendingAll ? "Sending..." : "📨 Send Initial Emails"}
        </button>
        <button
          onClick={handleSendDueFollowups}
          className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
        >
          🔁 Send Due Follow-ups
        </button>
      </div>

      {/* Add Contact */}
      <div className="bg-white border rounded-lg p-5 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-3">Add Contact</h3>
        {availableProspects.length === 0 ? (
          <p className="text-sm text-gray-400">
            All prospects are already in this campaign
          </p>
        ) : (
          <div className="flex gap-3">
            <select
              value={selectedProspectId}
              onChange={(e) => setSelectedProspectId(Number(e.target.value))}
              className="flex-1 border rounded px-3 py-2 text-sm"
            >
              <option value="">Select a prospect...</option>
              {availableProspects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} — {p.email}
                </option>
              ))}
            </select>
            <button
              onClick={handleAddContact}
              disabled={!selectedProspectId}
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              Add
            </button>
          </div>
        )}
      </div>

      {/* Contacts Table */}
      <div className="bg-white border rounded-lg p-5 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-3">
          Contacts ({contacts.length})
        </h3>
        {contacts.length === 0 ? (
          <p className="text-sm text-gray-400">No contacts yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Name</th>
                <th className="pb-2">Email</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Step</th>
                <th className="pb-2">Last Sent</th>
                <th className="pb-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((c) => (
                <tr key={c.prospect_id} className="border-b hover:bg-gray-50">
                  <td className="py-2 font-medium">{c.prospect_name}</td>
                  <td className="py-2 text-gray-500">{c.prospect_email}</td>
                  <td className="py-2">
                    <ContactStatusBadge status={c.status} />
                  </td>
                  <td className="py-2 text-center">{c.email_sequence_step}</td>
                  <td className="py-2 text-gray-400 text-xs">
                    {c.last_email_sent_at
                      ? new Date(c.last_email_sent_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="py-2">
                    <button
                      onClick={() => handleSendSingle(c.prospect_id)}
                      className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded hover:bg-blue-100"
                    >
                      Send Email
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Follow-ups */}
      <div className="bg-white border rounded-lg p-5 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-3">
          Scheduled Follow-ups ({followups.length})
        </h3>
        {followups.length === 0 ? (
          <p className="text-sm text-gray-400">No follow-ups scheduled</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Prospect</th>
                <th className="pb-2">Step</th>
                <th className="pb-2">Scheduled At</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {followups.map((f, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  <td className="py-2 font-medium">{f.prospect_name}</td>
                  <td className="py-2 text-center">{f.current_step}</td>
                  <td className="py-2 text-gray-500">
                    {new Date(f.scheduled_at).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">
                      {f.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
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

function ContactStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-gray-100 text-gray-600",
    contacted: "bg-blue-100 text-blue-700",
    replied: "bg-green-100 text-green-700",
    bounced: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] ?? "bg-gray-100"}`}
    >
      {status}
    </span>
  );
}

export default CampaignDetail;
