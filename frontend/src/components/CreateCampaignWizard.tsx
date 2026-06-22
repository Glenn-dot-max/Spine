/**
 * SPINE V1 — CreateCampaignWizard
 * Rôle : Wizard 5 pages pour créer une campagne post-salon.
 * Props : onClose (ferme le wizard), onCreated (callback après création)
 * Dépendances API : POST /api/campaigns/, GET /api/companies/
 * À faire : Pages 2-5 (catalogue, PJ, leads IA, templates)
 * Dernière modification : 2026-06-21 — Page 2 redesign avec distributeur picker + CC suggérés
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createCampaign } from "../api/campaigns";
import api from "../api/client";
import EmailPreviewModal from "./EmailPreviewModal";
import {
  getDistributors,
  getCompanyContacts,
  type CompanyContact,
} from "../api/companies";
import WizardCatalogueStep from "./WizardCatalogueStep";
import type { Company } from "../types";

type WizardProps = {
  onClose: () => void;
};

type ImportPreviewRow = {
  email?: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  position?: string;
  _already_exists?: boolean;
  [key: string]: unknown;
};

const STEPS = [
  "Salon context",
  "Distributor",
  "Catalogue",
  "Your message",
  "Import leads",
  "Attachments",
  "Review & Create",
  "Preview emails",
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

  // Step 2 — Distributeur
  is_distributor_show: false,
  distributor_company_id: null as number | null,
  distributor_name: "",
  auto_cc_sales_rep: false,
  cc_contact_ids: [] as number[],

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
  const [leadsFile, setLeadsFile] = useState<File | null>(null);
  const [leadsPreview, setLeadsPreview] = useState<{
    imported: number;
    skipped: number;
  } | null>(null);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [createdCampaignId, setCreatedCampaignId] = useState<number | null>(
    null,
  );
  const [importResults, setImportResults] = useState<
    { id: number; name: string }[]
  >([]);
  const [previewingProspect, setPreviewingProspect] = useState<{
    id: number;
    name: string;
  } | null>(null);
  const [importPreviewLoading, setImportPreviewLoading] = useState(false);
  const [importPreviewError, setImportPreviewError] = useState("");
  const [importPreviewWarnings, setImportPreviewWarnings] = useState<string[]>(
    [],
  );
  const [importPreviewRows, setImportPreviewRows] = useState<
    ImportPreviewRow[]
  >([]);
  const [importPreviewTotalRows, setImportPreviewTotalRows] = useState(0);
  const [distributors, setDistributors] = useState<Company[]>([]);
  const [companyContacts, setCompanyContacts] = useState<CompanyContact[]>([]);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);

  // Charger les distributeurs au montage du wizard
  useEffect(() => {
    getDistributors()
      .then(setDistributors)
      .catch(() => {});
  }, []);

  const set = (field: string, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  // Sélection d'un distributeur → charge ses contacts pour les CC suggérés
  const handleDistributorSelect = async (companyId: number | null) => {
    set("distributor_company_id", companyId);
    set("cc_contact_ids", []);
    setCompanyContacts([]);
    if (!companyId) {
      set("distributor_name", "");
      return;
    }
    const selected = distributors.find((d) => d.id === companyId);
    set("distributor_name", selected?.name ?? "");
    setLoadingContacts(true);
    try {
      const contacts = await getCompanyContacts(companyId);
      setCompanyContacts(contacts);
    } catch {
      // non-bloquant
    } finally {
      setLoadingContacts(false);
    }
  };

  const toggleCcContact = (contactId: number) => {
    const current = form.cc_contact_ids as number[];
    if (current.includes(contactId)) {
      set(
        "cc_contact_ids",
        current.filter((id) => id !== contactId),
      );
    } else {
      set("cc_contact_ids", [...current, contactId]);
    }
  };

  const loadLeadsFilePreview = async (file: File) => {
    setImportPreviewLoading(true);
    setImportPreviewError("");
    setImportPreviewWarnings([]);
    setImportPreviewRows([]);
    setImportPreviewTotalRows(0);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post("/api/prospects/import/preview", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportPreviewWarnings(res.data.warnings ?? []);
      setImportPreviewRows(res.data.sample_data ?? []);
      setImportPreviewTotalRows(res.data.total_rows ?? 0);
    } catch {
      setImportPreviewError(
        "Impossible d'analyser ce fichier. Vérifie que les colonnes email, first_name et last_name sont présentes.",
      );
    } finally {
      setImportPreviewLoading(false);
    }
  };

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
      if (form.distributor_company_id)
        payload.distributor_company_id = form.distributor_company_id;
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
      setCreatedCampaignId(created.id);

      // Import leads si fichier sélectionné
      if (leadsFile) {
        const formData = new FormData();
        formData.append("file", leadsFile);
        try {
          const res = await api.post(
            `/api/prospects/import?campaign_id=${created.id}`,
            formData,
            { headers: { "Content-Type": "multipart/form-data" } },
          );
          setLeadsPreview({
            imported: res.data.total_rows,
            skipped: res.data.skipped ?? 0,
          });
          // Peupler la liste de preview avec les prospects importés
          if (res.data.prospect_ids?.length > 0) {
            const contactsRes = await api.get(
              `/api/campaigns/${created.id}/contacts/`,
            );
            const contacts = contactsRes.data.map(
              (c: {
                prospect_id: number;
                first_name: string;
                last_name: string;
              }) => ({
                id: c.prospect_id,
                name: `${c.first_name} ${c.last_name}`,
              }),
            );
            setImportResults(contacts);
          }
        } catch {
          // non-bloquant
        }
      }

      // Upload des pièces jointes si présentes
      if (attachments.length > 0) {
        const attachFormData = new FormData();
        attachments.forEach((f) => attachFormData.append("files", f));
        try {
          await api.post(
            `/api/campaigns/${created.id}/attachments/`,
            attachFormData,
            { headers: { "Content-Type": "multipart/form-data" } },
          );
        } catch {
          // non-bloquant
        }
      }

      setStep(7);
    } catch {
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

          {/* PAGE 2 — Distributeur */}
          {step === 1 && (
            <>
              <p className="text-sm text-gray-500">
                Was this a distributor show? If so, select the distributor from
                your Companies to automatically link the campaign.
              </p>

              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id="is_distributor"
                  checked={form.is_distributor_show}
                  onChange={(e) => {
                    set("is_distributor_show", e.target.checked);
                    if (!e.target.checked) handleDistributorSelect(null);
                  }}
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
                  {/* Picker distributeur depuis Companies */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select distributor
                      <span className="ml-2 text-xs font-normal text-gray-400">
                        from your Companies (chain level = Distributor)
                      </span>
                    </label>
                    {distributors.length === 0 ? (
                      <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg text-sm text-yellow-700">
                        ⚠️ No distributor found in your Companies.{" "}
                        <a
                          href="/companies"
                          target="_blank"
                          className="underline font-medium"
                        >
                          Add one →
                        </a>
                      </div>
                    ) : (
                      <select
                        value={form.distributor_company_id ?? ""}
                        onChange={(e) =>
                          handleDistributorSelect(
                            e.target.value ? Number(e.target.value) : null,
                          )
                        }
                        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">— Select a distributor —</option>
                        {distributors.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name}
                            {d.market ? ` · ${d.market}` : ""}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  {/* CC suggérés depuis les contacts de la company */}
                  {form.distributor_company_id && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Suggested CC contacts
                        <span className="ml-2 text-xs font-normal text-gray-400">
                          from the distributor's contact list
                        </span>
                      </label>
                      {loadingContacts ? (
                        <p className="text-sm text-gray-400">
                          Loading contacts...
                        </p>
                      ) : companyContacts.length === 0 ? (
                        <p className="text-sm text-gray-400">
                          No contacts linked to this company yet.
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {companyContacts.map((c) => (
                            <div
                              key={c.id}
                              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                            >
                              <input
                                type="checkbox"
                                id={`cc-${c.id}`}
                                checked={(
                                  form.cc_contact_ids as number[]
                                ).includes(c.id)}
                                onChange={() => toggleCcContact(c.id)}
                                className="w-4 h-4 accent-blue-600"
                              />
                              <label
                                htmlFor={`cc-${c.id}`}
                                className="text-sm text-gray-700 flex-1 cursor-pointer"
                              >
                                <span className="font-medium">
                                  {[c.first_name, c.last_name]
                                    .filter(Boolean)
                                    .join(" ")}
                                </span>
                                {c.position && (
                                  <span className="ml-2 text-xs text-gray-400">
                                    {c.position}
                                  </span>
                                )}
                                <span className="block text-xs text-gray-400">
                                  {c.email}
                                </span>
                              </label>
                              <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">
                                CC
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

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

          {/* PAGE 3 — Catalogue */}
          {step === 2 && (
            <WizardCatalogueStep
              distributorCompanyId={form.distributor_company_id}
              distributorName={form.distributor_name}
              selectedProductIds={selectedProductIds}
              onSelectionChange={setSelectedProductIds}
              catalogPitchText={form.catalog_pitch_text}
              onPitchChange={(v) => set("catalog_pitch_text", v)}
              offerSamples={form.offer_samples}
              onOfferSamplesChange={(v) => set("offer_samples", v)}
              samplesNote={form.samples_note}
              onSamplesNoteChange={(v) => set("samples_note", v)}
            />
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

          {/* STEP 5 — Import leads */}
          {step === 4 && (
            <>
              <p className="text-sm text-gray-500">
                Import your contacts from the trade show. Accepted formats: CSV,
                XLSX, XLS.
              </p>

              <div
                onClick={() => document.getElementById("leads-upload")?.click()}
                className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition"
              >
                <p className="text-3xl mb-2">📋</p>
                {leadsFile ? (
                  <>
                    <p className="text-sm font-medium text-green-700">
                      ✅ {leadsFile.name}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Click to change
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-gray-600 font-medium">
                      Click to upload your leads file
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      CSV, XLSX, XLS - exporter from the show scanner
                    </p>
                  </>
                )}
                <input
                  id="leads-upload"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files?.[0] || null;
                    setLeadsFile(file);
                    if (!file) {
                      setImportPreviewWarnings([]);
                      setImportPreviewRows([]);
                      setImportPreviewTotalRows(0);
                      setImportPreviewError("");
                      return;
                    }
                    await loadLeadsFilePreview(file);
                  }}
                />
              </div>

              {leadsPreview && (
                <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                  ⏳ Importing contacts... This may take a moment.
                </div>
              )}

              {importPreviewError && (
                <div className="p-4 bg-red-50 rounded-lg text-sm text-red-700">
                  ❌ {importPreviewError}
                </div>
              )}

              {importPreviewTotalRows > 0 &&
                !importPreviewLoading &&
                !importPreviewError && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-green-50 rounded-lg text-sm text-green-700 flex-1">
                        ✅ <strong>{importPreviewTotalRows}</strong> contacts
                        detected in the file
                      </div>
                    </div>

                    {importPreviewWarnings.length > 0 && (
                      <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
                        <ul className="text-sm text-yellow-700 space-y-1">
                          {importPreviewWarnings.map((w, i) => (
                            <li key={`w-${i}`}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {importPreviewRows.length > 0 && (
                      <div className="border rounded-lg overflow-hidden">
                        <div className="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-500 uppercase tracking-wide">
                          Overlook of first five contacts in the file
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm">
                            <thead className="bg-white border-b">
                              <tr>
                                <th className="text-left px-3 py-2 text-gray-500 font-medium">
                                  Name
                                </th>
                                <th className="text-left px-3 py-2 text-gray-500 font-medium">
                                  Email
                                </th>
                                <th className="text-left px-3 py-2 text-gray-500 font-medium">
                                  Company
                                </th>
                                <th className="text-left px-3 py-2 text-gray-500 font-medium">
                                  Position
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {importPreviewRows.map((row, i) => (
                                <tr
                                  key={`${row.email ?? "row"}-${i}`}
                                  className="border-b last:border-0"
                                >
                                  <td className="px-3 py-2 text-gray-700">
                                    <span>
                                      {[row.first_name, row.last_name]
                                        .filter(Boolean)
                                        .join(" ") || "—"}
                                    </span>
                                    {row._already_exists && (
                                      <span className="ml-2 text-xs bg-yellow-500 text-yellow-700 px-1.5 py-0.5 rounded">
                                        (already in database)
                                      </span>
                                    )}
                                  </td>
                                  <td className="px-3 py-2 text-gray-500">
                                    {String(row.email || "-")}
                                  </td>
                                  <td className="px-3 py-2 text-gray-500">
                                    {String(row.company || "-")}
                                  </td>
                                  <td className="px-3 py-2 text-gray-500">
                                    {String(row.position || "-")}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}

              {!leadsFile && (
                <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-500">
                  💡 No file? No problem. You can add contacts one by one from
                  the
                </div>
              )}
            </>
          )}

          {/* STEP 6 — Attachments */}
          {step === 5 && (
            <>
              <p className="text-sm text-gray-500">
                Upload files to attach to your emails (catalogue, flyer, price
                list). Max 2 files × 5MB.
              </p>

              <div
                onClick={() =>
                  document.getElementById("attachments-upload")?.click()
                }
                className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition"
              >
                <p className="text-3xl mb-2">📎</p>
                <p className="text-sm text-gray-600 font-medium">
                  Click to upload attachments
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  PDF only — max 2 files, 5MB each
                </p>
                <input
                  id="attachments-upload"
                  type="file"
                  accept=".pdf"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []).slice(0, 2);
                    setAttachments(files);
                  }}
                />
              </div>

              {attachments.length > 0 && (
                <div className="space-y-2">
                  {attachments.map((f, i) => (
                    <div
                      key={i}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg text-sm"
                    >
                      <span className="text-gray-700">📄 {f.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {(f.size / 1024 / 1024).toFixed(1)} MB
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            setAttachments(
                              attachments.filter((_, j) => j !== i),
                            )
                          }
                          className="text-red-400 hover:text-red-600 text-xs"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                💡 Attachments will be sent with your emails. The filename will
                be mentioned automatically in the email body.
              </div>
            </>
          )}

          {/* STEP 7 — Review */}
          {step === 6 && (
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

          {/* STEP 8 — Preview emails */}
          {step === 7 && (
            <>
              <p className="text-sm text-gray-500">
                Preview the emails that will be sent to your contacts.
              </p>

              {importResults.length === 0 ? (
                <div className="p-4 bg-yellow-50 rounded-lg text-sm text-yellow-700">
                  ⚠️ No contacts imported — you can preview emails from the
                  campaign detail page once you add contacts.
                </div>
              ) : (
                <div className="space-y-2">
                  {importResults.map((p) => (
                    <div
                      key={p.id}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                    >
                      <span className="text-sm text-gray-700 font-medium">
                        {p.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => setPreviewingProspect(p)}
                        className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-lg hover:bg-blue-100"
                      >
                        👁 Preview emails
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="p-4 bg-green-50 rounded-lg text-sm text-green-700">
                ✅ Campaign created successfully! Click "Go to campaign" when
                ready.
              </div>
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

          {step === 6 ? (
            <button
              onClick={handleCreate}
              disabled={loading}
              className="px-5 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? "Creating..." : "✅ Create campaign"}
            </button>
          ) : step === 7 ? (
            <button
              onClick={() =>
                createdCampaignId && navigate(`/campaigns/${createdCampaignId}`)
              }
              className="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to campaign →
            </button>
          ) : (
            <button
              onClick={() => setStep(step + 1)}
              disabled={step === 0 && (!form.name || !form.event_date)}
              className="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          )}
        </div>

        {previewingProspect && createdCampaignId && (
          <EmailPreviewModal
            campaignId={createdCampaignId!}
            prospectId={previewingProspect.id}
            prospectName={previewingProspect.name}
            attachmentNames={attachments.map((f) => f.name)}
            onClose={() => setPreviewingProspect(null)}
          />
        )}
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
