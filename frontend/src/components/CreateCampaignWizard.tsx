/**
 * SPINE V1 — CreateCampaignWizard
 * Rôle : Wizard 5 étapes pour créer une campagne post-salon.
 * Props : onClose (ferme le wizard), onCreated (callback après création)
 * Dépendances API : POST /api/campaigns/
 * À faire : Step 5 preview par prospect (dans CampaignDetail)
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createCampaign } from "../api/campaigns";

type WizardProps = {
  onClose: () => void;
};

const STEPS = [
  "Salon context",
  "Distributor",
  "Catalogue",
  "Your message",
  "Review & Create",
];

const emptyForm = {
  // Step 1
  name: "",
  event_date: "",
  end_date: "",
  location: "",
  campaign_source: "trade_show",
  followup_delay_1: 5,
  followup_delay_2: 14,
  followup_delay_3: 21,

  // Step 2
  is_distributor_show: false,
  distributor_name: "",
  auto_cc_sales_rep: false,

  // Step 3
  catalog_pitch_text: "",
  offer_samples: false,
  samples_note: "",

  // Step 4
  company_intro_text: "",
  segment_note_global: "",
  segment_note_restaurant: "",
  segment_note_industry: "",
  segment_note_retail: "",
};

export default function CreateCampaignWizard({ onClose }: WizardProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (field: string, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleCreate = async () => {
    setLoading(true);
    setError("");
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        event_date: form.event_date,
        campaign_source: form.campaign_source,
        followup_delay_1: form.followup_delay_1,
        followup_delay_2: form.followup_delay_2,
        followup_delay_3: form.followup_delay_3,
        is_distributor_show: form.is_distributor_show,
        auto_cc_sales_rep: form.auto_cc_sales_rep,
        offer_samples: form.offer_samples,
      };
      if (form.end_date) payload.end_date = form.end_date;
      if (form.location) payload.location = form.location;
      if (form.distributor_name)
        payload.distributor_name = form.distributor_name;
      if (form.catalog_pitch_text)
        payload.catalog_pitch_text = form.catalog_pitch_text;
      if (form.samples_note) payload.samples_note = form.samples_note;
      if (form.company_intro_text)
        payload.company_intro_text = form.company_intro_text;
      if (form.segment_note_global)
        payload.segment_note_global = form.segment_note_global;
      if (form.segment_note_restaurant)
        payload.segment_note_restaurant = form.segment_note_restaurant;
      if (form.segment_note_industry)
        payload.segment_note_industry = form.segment_note_industry;
      if (form.segment_note_retail)
        payload.segment_note_retail = form.segment_note_retail;

      const created = await createCampaign(payload);
      navigate(`/campaigns/${created.id}`);
    } catch (e) {
      setError("Failed to create campaign. Please check required fields.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-800">New Campaign</h2>
            <p className="text-sm text-gray-400 mt-0.5">
              Step {step + 1} of {STEPS.length} — {STEPS[step]}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-gray-100">
          <div
            className="h-1 bg-blue-500 transition-all"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        {/* Step content */}
        <div className="p-6 space-y-4">
          {/* STEP 1 — Salon context */}
          {step === 0 && (
            <>
              <p className="text-sm text-gray-500">
                Tell us about the trade show.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign name *
                </label>
                <input
                  type="text"
                  placeholder="ex: NRA 2026"
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start date *
                  </label>
                  <input
                    type="date"
                    value={form.event_date}
                    onChange={(e) => set("event_date", e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End date
                  </label>
                  <input
                    type="date"
                    value={form.end_date}
                    onChange={(e) => set("end_date", e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  placeholder="ex: Chicago, IL"
                  value={form.location}
                  onChange={(e) => set("location", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source
                </label>
                <div className="flex gap-3">
                  {[
                    {
                      value: "trade_show",
                      label: "🎪 Trade Show",
                      active: true,
                    },
                    {
                      value: "ride_along",
                      label: "🚗 Ride Along",
                      active: false,
                    },
                    { value: "outreach", label: "📬 Outreach", active: false },
                  ].map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      disabled={!s.active}
                      onClick={() =>
                        s.active && set("campaign_source", s.value)
                      }
                      className={`flex-1 py-2 px-3 rounded-lg text-sm border transition ${
                        form.campaign_source === s.value
                          ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                          : s.active
                            ? "border-gray-200 text-gray-600 hover:border-gray-300"
                            : "border-gray-100 text-gray-300 cursor-not-allowed"
                      }`}
                    >
                      {s.label}
                      {!s.active && (
                        <span className="block text-xs mt-0.5 text-gray-300">
                          Coming soon
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Follow-up delays (days)
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { key: "followup_delay_1", label: "J+? (1st)" },
                    { key: "followup_delay_2", label: "J+? (2nd)" },
                    { key: "followup_delay_3", label: "J+? (3rd)" },
                  ].map(({ key, label }) => (
                    <div key={key}>
                      <label className="block text-xs text-gray-500 mb-1">
                        {label}
                      </label>
                      <input
                        type="number"
                        min={1}
                        value={form[key as keyof typeof form] as number}
                        onChange={(e) => set(key, Number(e.target.value))}
                        className="w-full border rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* STEP 2 — Distributor */}
          {step === 1 && (
            <>
              <p className="text-sm text-gray-500">
                Was this a distributor show? If so, all contacts are likely
                their customers.
              </p>

              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id="is_distributor"
                  checked={form.is_distributor_show}
                  onChange={(e) => set("is_distributor_show", e.target.checked)}
                  className="w-4 h-4 accent-blue-600"
                />
                <label
                  htmlFor="is_distributor"
                  className="text-sm font-medium text-gray-700"
                >
                  This was a distributor show
                </label>
              </div>

              {form.is_distributor_show && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Distributor name
                    </label>
                    <input
                      type="text"
                      placeholder="ex: Sysco, US Foods..."
                      value={form.distributor_name}
                      onChange={(e) => set("distributor_name", e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="auto_cc"
                      checked={form.auto_cc_sales_rep}
                      onChange={(e) =>
                        set("auto_cc_sales_rep", e.target.checked)
                      }
                      className="w-4 h-4 accent-blue-600"
                    />
                    <div>
                      <label
                        htmlFor="auto_cc"
                        className="text-sm font-medium text-gray-700"
                      >
                        Auto-CC the distributor sales rep
                      </label>
                      <p className="text-xs text-gray-400 mt-0.5">
                        If a sales rep is assigned to the prospect, they'll be
                        added in CC automatically
                      </p>
                    </div>
                  </div>
                </>
              )}

              {!form.is_distributor_show && (
                <div className="p-4 bg-yellow-50 border border-yellow-100 rounded-lg text-sm text-yellow-700">
                  💡 National show? You'll be able to specify which distributors
                  each contact works with from the campaign detail page.
                </div>
              )}
            </>
          )}

          {/* STEP 3 — Catalogue */}
          {step === 2 && (
            <>
              <p className="text-sm text-gray-500">
                How do you want to present your catalogue in the emails?
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Catalogue pitch
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    (leave empty for generic fallback)
                  </span>
                </label>
                <textarea
                  rows={4}
                  placeholder="ex: Our catalogue includes premium European charcuterie and cheese, designed for high-end foodservice and retail operations..."
                  value={form.catalog_pitch_text}
                  onChange={(e) => set("catalog_pitch_text", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  If left empty: "Please find our product catalogue attached —
                  you'll find our full range of references."
                </p>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="offer_samples"
                    checked={form.offer_samples}
                    onChange={(e) => set("offer_samples", e.target.checked)}
                    className="w-4 h-4 accent-blue-600"
                  />
                  <label
                    htmlFor="offer_samples"
                    className="text-sm font-medium text-gray-700"
                  >
                    Offer product samples in the email
                  </label>
                </div>

                {form.offer_samples && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Samples details / instructions
                    </label>
                    <textarea
                      rows={2}
                      placeholder="ex: Just send us your shipping address and we'll get samples out within 48h."
                      value={form.samples_note}
                      onChange={(e) => set("samples_note", e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
                    />
                  </div>
                )}
              </div>
            </>
          )}

          {/* STEP 4 — Your message */}
          {step === 3 && (
            <>
              <p className="text-sm text-gray-500">
                Personalize the email body. All fields are optional — leave
                empty for smart defaults.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company intro
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    Who are you? What do you do?
                  </span>
                </label>
                <textarea
                  rows={3}
                  placeholder="ex: We are a specialty food importer focused on premium European products, working with distributors and foodservice operators across North America."
                  value={form.company_intro_text}
                  onChange={(e) => set("company_intro_text", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Global note
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    Added to all emails regardless of client type
                  </span>
                </label>
                <textarea
                  rows={2}
                  placeholder="ex: We are currently expanding our distribution network..."
                  value={form.segment_note_global}
                  onChange={(e) => set("segment_note_global", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
                />
              </div>

              <div className="border-t pt-4 space-y-3">
                <p className="text-sm font-medium text-gray-700">
                  Segment-specific notes
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    Only added if client type matches
                  </span>
                </p>

                {[
                  {
                    key: "segment_note_restaurant",
                    label: "🍽 Foodservice / Restaurant",
                    placeholder:
                      "ex: Our formats are designed for high-volume kitchens...",
                  },
                  {
                    key: "segment_note_industry",
                    label: "🏭 Industry",
                    placeholder:
                      "ex: We offer private label and bulk formats...",
                  },
                  {
                    key: "segment_note_retail",
                    label: "🛒 Retail",
                    placeholder:
                      "ex: Strong margin potential and proven shelf performance...",
                  },
                ].map(({ key, label, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      {label}
                    </label>
                    <textarea
                      rows={2}
                      placeholder={placeholder}
                      value={form[key as keyof typeof form] as string}
                      onChange={(e) => set(key, e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
                    />
                  </div>
                ))}
              </div>
            </>
          )}

          {/* STEP 5 — Review */}
          {step === 4 && (
            <>
              <p className="text-sm text-gray-500">
                Review your campaign before creating it.
              </p>

              <div className="space-y-3 text-sm">
                <ReviewRow label="Name" value={form.name} />
                <ReviewRow
                  label="Date"
                  value={`${form.event_date}${form.end_date ? ` → ${form.end_date}` : ""}`}
                />
                <ReviewRow label="Location" value={form.location || "—"} />
                <ReviewRow label="Source" value={form.campaign_source} />
                <ReviewRow
                  label="Follow-ups"
                  value={`J+${form.followup_delay_1} / J+${form.followup_delay_2} / J+${form.followup_delay_3}`}
                />
                <ReviewRow
                  label="Distributor show"
                  value={
                    form.is_distributor_show
                      ? `Yes — ${form.distributor_name || "unnamed"}`
                      : "No"
                  }
                />
                <ReviewRow
                  label="Offer samples"
                  value={form.offer_samples ? "Yes" : "No"}
                />
                <ReviewRow
                  label="Company intro"
                  value={
                    form.company_intro_text
                      ? "✅ Custom text set"
                      : "⚠️ Not set — bloc will be omitted"
                  }
                  muted={!form.company_intro_text}
                />
                <ReviewRow
                  label="Catalogue pitch"
                  value={
                    form.catalog_pitch_text
                      ? "✅ Custom text set"
                      : "ℹ️ Generic fallback will be used"
                  }
                  muted={!form.catalog_pitch_text}
                />
              </div>

              <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                💡 After creating the campaign, go to the campaign detail page
                to import your contacts and preview the emails.
              </div>

              {error && (
                <p className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">
                  {error}
                </p>
              )}
            </>
          )}
        </div>

        {/* Footer nav */}
        <div className="flex justify-between items-center p-6 border-t bg-gray-50">
          <button
            onClick={() => (step === 0 ? onClose() : setStep(step - 1))}
            className="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-white"
          >
            {step === 0 ? "Cancel" : "← Back"}
          </button>

          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={step === 0 && (!form.name || !form.event_date)}
              className="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={loading}
              className="px-5 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? "Creating..." : "✅ Create campaign"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ReviewRow({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-500 w-36 shrink-0">{label}</span>
      <span
        className={`text-right ${muted ? "text-gray-400" : "text-gray-800 font-medium"}`}
      >
        {value}
      </span>
    </div>
  );
}
