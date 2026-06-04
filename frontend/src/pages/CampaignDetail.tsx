import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getCampaign,
  getCampaignContacts,
  addContactToCampaign,
  sendInitialEmails,
  getScheduledFollowups,
  sendDueFollowups,
} from "../api/campaigns";
import { getProspects } from "../api/prospects";
import api from "../api/client";
import type { Campaign, CampaignContact, Prospect } from "../types";
import EmailPreviewModal from "../components/EmailPreviewModal";

function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const campaignId = Number(id);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [contacts, setContacts] = useState<CampaignContact[]>([]);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [followups, setFollowups] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProspectId, setSelectedProspectId] = useState<number | "">("");
  const [sendingAll, setSendingAll] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [previewingContact, setPreviewingContact] = useState<{
    id: number;
    name: string;
  } | null>(null);
  const [previewAttachmentNames, setPreviewAttachmentNames] = useState<
    string[]
  >([]);

  useEffect(() => {
    fetchAll();
  }, [campaignId]);

  const fetchAll = async () => {
    try {
      const [camp, ctcts, prosps] = await Promise.all([
        getCampaign(campaignId),
        getCampaignContacts(campaignId),
        getProspects(),
      ]);
      setCampaign(camp);
      setContacts(ctcts);
      setProspects(prosps);

      try {
        const fups = await getScheduledFollowups(campaignId);
        setFollowups(
          Array.isArray(fups) ? fups : (fups.scheduled_followups ?? []),
        );
      } catch {
        setFollowups([]);
      }
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
      await sendDueFollowups(campaignId);
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
          disabled={campaign.status !== "upcoming"}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {sendingAll ? "Sending..." : "📨 Send Initial Emails"}
        </button>
      </div>

      {/* Campaign Info */}
      <div className="bg-white border rounded-lg p-5 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-4">Campaign Info</h3>
        <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 mb-4">
          <div>
            <span className="text-gray-400">📍 Location</span>
            <p className="font-medium">{campaign.location || "—"}</p>
          </div>
          <div>
            <span className="text-gray-400">🏢 Distributor</span>
            <p className="font-medium">{campaign.distributor_name || "—"}</p>
          </div>
          <div>
            <span className="text-gray-400">📅 Start Date</span>
            <p className="font-medium">{campaign.event_date}</p>
          </div>
          <div>
            <span className="text-gray-400">📅 End Date</span>
            <p className="font-medium">{campaign.end_date || "—"}</p>
          </div>
          <div className="col-span-2">
            <span className="text-gray-400">📝 Description</span>
            <p className="font-medium">{campaign.description || "—"}</p>
          </div>
        </div>
        <div className="border-t pt-3">
          <p className="text-xs text-gray-400 mb-2 font-medium">
            Follow-up delays
          </p>
          <div className="flex gap-3">
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              🔁 Followup 1 = D+{campaign.followup_delay_1}
            </span>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              🔁 Followup 2 = D+{campaign.followup_delay_2}
            </span>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              🔁 Followup 3 = D+{campaign.followup_delay_3}
            </span>
          </div>
        </div>
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
        <div className="flex justify-between items-start mb-4">
          <h3 className="font-semibold text-gray-800">
            Contacts ({contacts.length})
          </h3>
          <div className="w-72">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              📎 Attachment names for preview
              <span className="ml-1 text-gray-400">(comma-separated)</span>
            </label>
            <input
              type="text"
              placeholder="ex: catalogue_2026.pdf, price_list.pdf"
              className="w-full border rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) =>
                setPreviewAttachmentNames(
                  e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                )
              }
            />
          </div>
        </div>

        {contacts.length === 0 ? (
          <p className="text-sm text-gray-400">No contacts yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 text-center">Name</th>
                <th className="pb-2 text-center">Email</th>
                <th className="pb-2 text-center">Status</th>
                <th className="pb-2 text-center">Next Step</th>
                <th className="pb-2 text-center">Last Sent</th>
                <th className="pb-2 text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((c) => (
                <tr key={c.prospect_id} className="border-b hover:bg-gray-50">
                  <td className="py-2 font-medium text-center">
                    {c.first_name} {c.last_name}
                  </td>
                  <td className="py-2 text-gray-500 text-center">{c.email}</td>
                  <td className="py-2 text-center">
                    <ContactStatusBadge status={c.status} />
                  </td>
                  <td className="py-2 text-center">
                    {[
                      "Initial",
                      "Follow-up 1",
                      "Follow-up 2",
                      "Follow-up 3",
                      "✅ Done",
                    ][c.email_sequence_step] ?? "-"}
                  </td>
                  <td className="py-2 text-gray-400 text-xs text-center">
                    {c.last_email_sent_at
                      ? new Date(c.last_email_sent_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="py-2 text-center">
                    <button
                      onClick={() => handleSendSingle(c.prospect_id)}
                      disabled={
                        c.email_sequence_step >= 4 ||
                        campaign.status === "completed"
                      }
                      className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Send Email
                    </button>
                    <button
                      onClick={() =>
                        setPreviewingContact({
                          id: c.prospect_id,
                          name: `${c.first_name} ${c.last_name}`,
                        })
                      }
                      className="text-xs bg-gray-50 text-gray-600 px-2 py-1 rounded hover:bg-gray-100"
                    >
                      👁 Preview
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
                <th className="pb-2 text-center">Prospect</th>
                <th className="pb-2 text-center">Next Step</th>
                <th className="pb-2 text-center">Scheduled At</th>
                <th className="pb-2 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {followups.map((f, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  <td className="py-2 font-medium text-center">
                    {String(f.prospect_name)}
                  </td>
                  <td className="py-2 text-center">
                    {["Initial", "Follow-up 1", "Follow-up 2", "Follow-up 3"][
                      Number(f.current_step)
                    ] ?? "-"}
                  </td>
                  <td className="py-2 text-gray-500 text-center">
                    {new Date(f.scheduled_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 text-center">
                    <span className="text-sm text-gray-600">
                      {String(f.status) === "pending"
                        ? "⏳ Pending"
                        : String(f.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Email Preview Modal */}
      {previewingContact && (
        <EmailPreviewModal
          campaignId={campaignId}
          prospectId={previewingContact.id}
          prospectName={previewingContact.name}
          attachmentNames={previewAttachmentNames}
          onClose={() => setPreviewingContact(null)}
        />
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

function ContactStatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    pending: "⏳ Pending",
    contacted: "📧 Contacted",
    replied: "✅ Replied",
    bounced: "❌ Bounced",
  };
  return (
    <span className="text-sm text-gray-600 text-center block">
      {labels[status] ?? status}
    </span>
  );
}

export default CampaignDetail;
