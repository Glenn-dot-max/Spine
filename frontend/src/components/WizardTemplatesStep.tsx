/**
 * SPINE V1 — WizardTemplatesStep
 * Role: Step 7 of campaign wizard — per-prospect email preview with inline editing.
 *       Tab selector for each email category (Initial, Follow-up 1/2/3).
 *       Each lead card shows the rendered email body with variable substitution.
 *       Click the body to edit it directly. "Reset" restores the base template.
 * Props:
 *   - ccContacts      : contacts suggested as CC (from distributor step)
 *   - attachments     : files with linked product IDs (from step 6)
 *   - stagedRows      : enriched leads (for rendering personalized previews)
 *   - campaignName    : used for {{campaign.name}} substitution
 *   - followupDelays  : [delay1, delay2, delay3] in days, displayed in tab labels
 * Dependencies: GET /api/templates, PUT /api/templates/:id, POST /api/templates
 * Last modified: 2026-06-22 — full redesign as per-prospect email preview cards
 */
import { useState, useEffect } from "react";
import { getTemplates, updateTemplate, createTemplate } from "../api/template";
import type { CompanyContact } from "../api/companies";
import type { EnrichedRow } from "../api/prospectImport";
import { improveEmail } from "../api/aiTools";

// ─── Types ────────────────────────────────────────────────────────────────────

type Category = "initial" | "followup_1" | "followup_2" | "followup_3";

type TemplateData = {
  id?: number;
  category: Category;
  subject_template: string;
  body_template: string;
};

type Props = {
  ccContacts: CompanyContact[];
  attachments: { file: File; linkedProductIds: number[] }[];
  stagedRows: EnrichedRow[];
  campaignName?: string;
  followupDelays?: [number, number, number];
};

// ─── Constants ────────────────────────────────────────────────────────────────

const CATEGORIES: Category[] = [
  "initial",
  "followup_1",
  "followup_2",
  "followup_3",
];

const CATEGORY_LABELS: Record<Category, string> = {
  initial: "Initial",
  followup_1: "Follow-up 1",
  followup_2: "Follow-up 2",
  followup_3: "Follow-up 3",
};

const DEFAULT_TEMPLATES: Record<
  Category,
  { subject_template: string; body_template: string }
> = {
  initial: {
    subject_template: "Great meeting you at {{campaign.name}}!",
    body_template:
      "Hi {{prospect.first_name}},\n\nIt was great meeting you at {{campaign.name}}!\n\nI wanted to follow up on our conversation and share more about what we offer.\n\nWould you be available for a quick call this week?\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_1: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nI wanted to follow up on my previous email regarding {{campaign.name}}.\n\nDid you get a chance to review our discussion?\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_2: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nJust checking in one more time about {{campaign.name}}.\n\nI'd love to connect and explore how we can help {{prospect.company_name}}.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_3: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nThis will be my last follow-up regarding {{campaign.name}}.\n\nIf the timing isn't right, no worries — feel free to reach out whenever you're ready.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
};

// Badge color by type_structure value
const TYPE_BADGE: Record<string, string> = {
  end_user: "bg-amber-100 text-amber-700",
  restaurant: "bg-orange-100 text-orange-700",
  distributor: "bg-blue-100 text-blue-700",
  importer: "bg-indigo-100 text-indigo-700",
  broker: "bg-purple-100 text-purple-700",
  industry: "bg-green-100 text-green-700",
  retail: "bg-pink-100 text-pink-700",
  other: "bg-gray-100 text-gray-600",
};

// ─── Variable substitution helpers ───────────────────────────────────────────

const renderBody = (
  tpl: string,
  row: EnrichedRow,
  campaignName: string,
): string =>
  tpl
    .replace(/\{\{prospect\.first_name\}\}/g, row.first_name ?? "there")
    .replace(
      /\{\{prospect\.company_name\}\}/g,
      row.company_name ?? "your company",
    )
    .replace(/\{\{campaign\.name\}\}/g, campaignName);

const renderSubject = (tpl: string, campaignName: string): string =>
  tpl.replace(/\{\{campaign\.name\}\}/g, campaignName);

// ─── Component ───────────────────────────────────────────────────────────────

export default function WizardTemplatesStep({
  ccContacts,
  attachments,
  stagedRows,
  campaignName = "the show",
  followupDelays = [5, 14, 21],
}: Props) {
  const [activeTab, setActiveTab] = useState<Category>("initial");
  const [templates, setTemplates] = useState<Record<Category, TemplateData>>(
    {} as Record<Category, TemplateData>,
  );
  const [loading, setLoading] = useState(true);
  const [savingTab, setSavingTab] = useState<Category | null>(null);
  const [savedTab, setSavedTab] = useState<Category | null>(null);

  // Per-lead body overrides: { "row_index": { "initial": "custom body...", ... } }
  const [leadOverrides, setLeadOverrides] = useState<
    Record<string, Partial<Record<Category, string>>>
  >({});

  // Which card is currently in edit mode: "rowIndex-category"
  const [editingKey, setEditingKey] = useState<string | null>(null);

  // Jey of the card currently being improved by AI: "rowIndex-category"
  const [improvingKey, setImprovingKey] = useState<string | null>(null);

  // Delay label per tab
  const delayLabel: Record<Category, string> = {
    initial: "J+0",
    followup_1: `J+${followupDelays[0]}`,
    followup_2: `J+${followupDelays[1]}`,
    followup_3: `J+${followupDelays[2]}`,
  };

  // Load templates from API on mount, fallback to defaults
  useEffect(() => {
    const load = async () => {
      try {
        const data = await getTemplates();
        const result = {} as Record<Category, TemplateData>;
        for (const cat of CATEGORIES) {
          // Prefer user-specific template, then any global, then hardcoded default
          const existing =
            data.find(
              (t: { category: string; user_id: number | null }) =>
                t.category === cat && t.user_id !== null,
            ) ?? data.find((t: { category: string }) => t.category === cat);

          result[cat] = {
            id: existing?.id,
            category: cat,
            subject_template:
              existing?.subject_template ??
              DEFAULT_TEMPLATES[cat].subject_template,
            body_template:
              existing?.body_template ?? DEFAULT_TEMPLATES[cat].body_template,
          };
        }
        setTemplates(result);
      } catch {
        const result = {} as Record<Category, TemplateData>;
        for (const cat of CATEGORIES) {
          result[cat] = { category: cat, ...DEFAULT_TEMPLATES[cat] };
        }
        setTemplates(result);
      } finally {
        setLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Get the body for a specific lead + category (override or rendered template)
  const getBody = (row: EnrichedRow, cat: Category): string => {
    const override = leadOverrides[String(row.row_index)]?.[cat];
    if (override !== undefined) return override;
    const tpl = templates[cat];
    if (!tpl) return "";
    return renderBody(tpl.body_template, row, campaignName);
  };

  // Update per-lead override
  const setBody = (row: EnrichedRow, cat: Category, value: string) => {
    setLeadOverrides((prev) => ({
      ...prev,
      [String(row.row_index)]: {
        ...(prev[String(row.row_index)] ?? {}),
        [cat]: value,
      },
    }));
  };

  // Reset per-lead override back to rendered template
  const resetBody = (row: EnrichedRow, cat: Category) => {
    setLeadOverrides((prev) => {
      const updated = { ...prev };
      if (updated[String(row.row_index)]) {
        const copy = { ...updated[String(row.row_index)] };
        delete copy[cat];
        updated[String(row.row_index)] = copy;
      }
      return updated;
    });
  };

  // Send the current body to Haiku and replace it with the improved version
  const handleImprove = async (row: EnrichedRow, cat: Category) => {
    const rowKey = String(row.row_index);
    const editKey = `${rowKey}-${cat}`;
    const currentBody = getBody(row, cat);
    setImprovingKey(editKey);
    try {
      const improved = await improveEmail(currentBody);
      setBody(row, cat, improved);
    } catch {
      // non-blocking
    } finally {
      setImprovingKey(null);
    }
  };

  // Save the active tab's template to the API
  const saveTemplate = async (cat: Category) => {
    const tpl = templates[cat];
    if (!tpl) return;
    setSavingTab(cat);
    try {
      if (tpl.id) {
        await updateTemplate(tpl.id, {
          subject_template: tpl.subject_template,
          body_template: tpl.body_template,
        });
      } else {
        const created = await createTemplate({
          name: `Campaign — ${CATEGORY_LABELS[cat]}`,
          category: cat,
          subject_template: tpl.subject_template,
          body_template: tpl.body_template,
        });
        setTemplates((prev) => ({
          ...prev,
          [cat]: { ...prev[cat], id: created.id },
        }));
      }
      setSavedTab(cat);
      setTimeout(() => setSavedTab(null), 2000);
    } catch {
      // non-blocking
    } finally {
      setSavingTab(null);
    }
  };

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">
        Loading templates...
      </div>
    );
  }

  const currentTpl = templates[activeTab];

  return (
    <div className="space-y-4">
      {/* ── Tab bar ───────────────────────────────────────────────────── */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => {
              setActiveTab(cat);
              setEditingKey(null);
            }}
            className={`flex-1 py-2 text-xs font-medium rounded-lg transition ${
              activeTab === cat
                ? "bg-white text-blue-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {CATEGORY_LABELS[cat]}
            <span
              className={`block font-normal ${activeTab === cat ? "text-blue-400" : "text-gray-400"}`}
            >
              {delayLabel[cat]}
            </span>
          </button>
        ))}
      </div>

      {/* ── Subject line ──────────────────────────────────────────────── */}
      {currentTpl && (
        <div className="border border-gray-200 rounded-xl bg-white p-4 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Subject line
            </p>
            <button
              type="button"
              onClick={() => saveTemplate(activeTab)}
              disabled={savingTab === activeTab}
              className="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              {savingTab === activeTab
                ? "Saving..."
                : savedTab === activeTab
                  ? "✓ Saved"
                  : "Save template"}
            </button>
          </div>
          <input
            type="text"
            value={currentTpl.subject_template}
            onChange={(e) =>
              setTemplates((prev) => ({
                ...prev,
                [activeTab]: {
                  ...prev[activeTab],
                  subject_template: e.target.value,
                },
              }))
            }
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400">
            Preview:{" "}
            <span className="text-gray-600 font-medium">
              {renderSubject(currentTpl.subject_template, campaignName)}
            </span>
          </p>
        </div>
      )}

      {/* ── CC + Attachments context bar ──────────────────────────────── */}
      {(ccContacts.length > 0 || attachments.length > 0) && (
        <div className="flex gap-3 flex-wrap">
          {ccContacts.length > 0 && (
            <div className="flex-1 p-3 bg-blue-50 border border-blue-100 rounded-lg min-w-0">
              <p className="text-xs font-semibold text-blue-700 mb-1">
                📋 CC on all emails
              </p>
              {ccContacts.map((c) => (
                <p key={c.id} className="text-xs text-gray-600 truncate">
                  {[c.first_name, c.last_name].filter(Boolean).join(" ")} ·{" "}
                  {c.email}
                </p>
              ))}
            </div>
          )}
          {attachments.length > 0 && (
            <div className="flex-1 p-3 bg-gray-50 border border-gray-200 rounded-lg min-w-0">
              <p className="text-xs font-semibold text-gray-600 mb-1">
                📎 Attachments
              </p>
              {attachments.map((a, i) => (
                <p key={i} className="text-xs text-gray-600 truncate">
                  {a.file.name}{" "}
                  <span className="text-gray-400">
                    ({(a.file.size / 1024 / 1024).toFixed(1)} MB)
                  </span>
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Per-lead email cards ───────────────────────────────────────── */}
      {stagedRows.length === 0 ? (
        <div className="p-4 bg-yellow-50 border border-yellow-100 rounded-lg text-sm text-yellow-700">
          ⚠️ No leads staged yet — go back to step 5 to import leads first.
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs font-medium text-gray-400">
            {stagedRows.length} lead{stagedRows.length > 1 ? "s" : ""} — click
            any email body to edit
          </p>

          {stagedRows.map((row) => {
            const rowKey = String(row.row_index);
            const editKey = `${rowKey}-${activeTab}`;
            const isEditing = editingKey === editKey;
            const body = getBody(row, activeTab);
            const hasOverride =
              leadOverrides[rowKey]?.[activeTab] !== undefined;
            const typeStructure = row.category?.type_structure ?? "other";
            const badgeClass = TYPE_BADGE[typeStructure] ?? TYPE_BADGE.other;
            const typeLabel = typeStructure.replace(/_/g, " ");

            // Attachments that are linked to any of this lead's matched products
            const linkedAttachments = attachments.filter((a) =>
              a.linkedProductIds.some((pid) =>
                row.product_matches.some((pm) => pm.product_id === pid),
              ),
            );

            return (
              <div
                key={rowKey}
                className="border border-gray-200 rounded-xl bg-white overflow-hidden"
              >
                {/* Lead header */}
                <div className="flex items-start justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                  <div className="space-y-1">
                    {/* Name + type badges */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-gray-800">
                        {[row.first_name, row.company_name]
                          .filter(Boolean)
                          .join(" — ")}
                      </span>
                      {typeLabel && (
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${badgeClass}`}
                        >
                          {typeLabel}
                        </span>
                      )}
                      {row.category?.segment && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-100">
                          {row.category.segment}
                        </span>
                      )}
                    </div>
                    {/* Email + products */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {row.email && (
                        <span className="text-xs text-gray-400">
                          ✉ {row.email}
                        </span>
                      )}
                      {row.product_matches.slice(0, 3).map((p) => (
                        <span
                          key={p.product_id}
                          className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600"
                        >
                          {p.product_name}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Override indicator */}
                  {hasOverride && (
                    <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full shrink-0">
                      edited
                    </span>
                  )}
                </div>

                {/* Email body — click to edit */}
                <div
                  className={`px-4 py-3 cursor-text ${isEditing ? "" : "hover:bg-gray-50 transition"}`}
                  onClick={() => {
                    if (!isEditing) setEditingKey(editKey);
                  }}
                >
                  {isEditing ? (
                    <div className="space-y-2">
                      <textarea
                        autoFocus
                        value={body}
                        onChange={(e) =>
                          setBody(row, activeTab, e.target.value)
                        }
                        rows={9}
                        className="w-full border border-blue-300 rounded-lg px-3 py-2 text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-blue-400 bg-blue-50"
                      />
                      <div className="flex justify-end gap-2">
                        {hasOverride && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              resetBody(row, activeTab);
                            }}
                            className="text-xs px-3 py-1 border border-gray-200 rounded-lg text-gray-500 hover:bg-gray-50"
                          >
                            Reset to template
                          </button>
                        )}
                        <button
                          type="button"
                          disabled={improvingKey === editKey}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleImprove(row, activeTab);
                          }}
                          className="text-xs px-3 py-1 border border-purple-200 text-purple-700 bg-purple-50 rounded-lg hover:bg-purple-100 disabled:opacity-50 flex items-center gap-1"
                        >
                          {improvingKey === editKey ? (
                            <> ⏳ Improving...</>
                          ) : (
                            <>✨ Improve with AI</>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingKey(null);
                          }}
                          className="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          Done
                        </button>
                      </div>
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                      {body}
                    </pre>
                  )}
                </div>

                {/* Product-linked attachments for this lead */}
                {linkedAttachments.length > 0 && (
                  <div className="px-4 pb-3 flex gap-2 flex-wrap">
                    {linkedAttachments.map((a, i) => (
                      <span key={i} className="text-xs text-gray-400">
                        📎 {a.file.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
