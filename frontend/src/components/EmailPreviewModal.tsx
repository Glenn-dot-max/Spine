/**
 * SPINE V1 — EmailPreviewModal
 * Rôle : Preview des 3 emails d'une séquence pour un prospect.
 *        Affiche les blocs éditables séparément + HTML assemblé.
 *        L'user peut modifier chaque bloc et régénérer le preview.
 * Props : campaignId, prospectId, prospectName, attachmentNames, onClose
 * Dépendances API : POST /campaigns/{id}/contacts/{id}/emails/preview
 */
import { useEffect, useState } from "react";
import { previewEmailWithOverrides } from "../api/campaigns";

type Step = 0 | 1 | 2;

const STEP_LABELS: Record<Step, string> = {
  0: "J0 — Initial",
  1: "J+? — Follow-up 1",
  2: "J+? — Follow-up 2",
};

const BLOCK_LABELS: Record<string, string> = {
  greeting: "👋 Greeting",
  company_intro: "🏢 Company intro",
  catalog_pitch: "📦 Catalogue pitch",
  segment_note: "🎯 Segment note",
  samples: "🎁 Samples offer",
  attachments: "📎 Attachments mention",
  cta: "📣 Call to action",
  signature: "✍️ Signature",
};

interface Props {
  campaignId: number;
  prospectId: number;
  prospectName: string;
  attachmentNames?: string[];
  onClose: () => void;
}

export default function EmailPreviewModal({
  campaignId,
  prospectId,
  prospectName,
  attachmentNames = [],
  onClose,
}: Props) {
  const [activeStep, setActiveStep] = useState<Step>(0);
  const [view, setView] = useState<"blocks" | "html">("blocks");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [previews, setPreviews] = useState<
    Record<
      number,
      {
        subject: string;
        html_body: string;
        blocks: Record<string, string | null>;
      } | null
    >
  >({});

  // Overrides : ce que l'user a modifié manuellement
  const [overrides, setOverrides] = useState<
    Record<number, Record<string, string>>
  >({
    0: {},
    1: {},
    2: {},
  });

  useEffect(() => {
    loadPreview(activeStep);
  }, [activeStep]);

  const loadPreview = async (step: Step, forceReload = false) => {
    if (previews[step] && !forceReload) return;
    setLoading(true);
    setError(null);
    try {
      const data = await previewEmailWithOverrides(
        campaignId,
        prospectId,
        step,
        overrides[step] || {},
        attachmentNames,
      );
      setPreviews((prev) => ({
        ...prev,
        [step]: {
          subject: data.subject,
          html_body: data.html_body,
          blocks: data.variables_used,
        },
      }));
    } catch {
      setError("Failed to load email preview.");
    } finally {
      setLoading(false);
    }
  };

  const handleBlockChange = (blockKey: string, value: string) => {
    setOverrides((prev) => ({
      ...prev,
      [activeStep]: { ...prev[activeStep], [blockKey]: value },
    }));
  };

  const handleRegenerate = () => {
    setPreviews((prev) => ({ ...prev, [activeStep]: null }));
    loadPreview(activeStep, true);
  };

  const current = previews[activeStep];
  // Merge generated blocks with user overrides for display
  const displayBlocks = current
    ? { ...current.blocks, ...overrides[activeStep] }
    : null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <div>
            <h2 className="font-semibold text-gray-800">Email Preview</h2>
            <p className="text-xs text-gray-500">{prospectName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Step tabs */}
        <div className="flex gap-1 px-6 pt-3 border-b">
          {([0, 1, 2] as Step[]).map((step) => (
            <button
              key={step}
              onClick={() => setActiveStep(step)}
              className={`px-4 py-2 text-sm font-medium rounded-t transition ${
                activeStep === step
                  ? "bg-blue-50 border border-b-white border-blue-200 text-blue-600 -mb-px"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {STEP_LABELS[step]}
            </button>
          ))}
        </div>

        {/* View toggle */}
        <div className="flex gap-2 px-6 py-3 bg-gray-50 border-b">
          <button
            onClick={() => setView("blocks")}
            className={`text-xs px-3 py-1 rounded-full ${view === "blocks" ? "bg-blue-600 text-white" : "bg-white border text-gray-500"}`}
          >
            ✏️ Edit blocks
          </button>
          <button
            onClick={() => setView("html")}
            className={`text-xs px-3 py-1 rounded-full ${view === "html" ? "bg-blue-600 text-white" : "bg-white border text-gray-500"}`}
          >
            👁 Preview HTML
          </button>
          {Object.keys(overrides[activeStep] || {}).length > 0 && (
            <button
              onClick={handleRegenerate}
              className="ml-auto text-xs px-3 py-1 rounded-full bg-green-600 text-white"
            >
              🔄 Apply changes
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && (
            <p className="text-sm text-gray-400 py-8 text-center">
              Loading preview...
            </p>
          )}
          {error && <p className="text-sm text-red-500">{error}</p>}

          {!loading && current && (
            <>
              {/* Subject */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={
                    overrides[activeStep]?.subject ?? current.subject ?? ""
                  }
                  onChange={(e) => handleBlockChange("subject", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder={
                    activeStep > 0 ? "Threading — no new subject needed" : ""
                  }
                />
                {activeStep > 0 && !overrides[activeStep]?.subject && (
                  <p className="text-xs text-gray-400 mt-1">
                    ℹ️ Follow-up will reply in the same thread (Re:)
                    automatically
                  </p>
                )}
              </div>

              {/* Blocks edit view */}
              {view === "blocks" && displayBlocks && (
                <div className="space-y-3">
                  {Object.entries(BLOCK_LABELS).map(([key, label]) => {
                    const value = displayBlocks[key];
                    if (value === null || value === undefined)
                      return (
                        <div
                          key={key}
                          className="opacity-40 text-xs text-gray-400 py-1"
                        >
                          {label} — <em>not included (condition not met)</em>
                        </div>
                      );
                    return (
                      <div key={key}>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          {label}
                        </label>
                        <textarea
                          rows={key === "greeting" || key === "cta" ? 3 : 4}
                          value={overrides[activeStep]?.[key] ?? value}
                          onChange={(e) =>
                            handleBlockChange(key, e.target.value)
                          }
                          className="w-full border rounded-lg px-3 py-2 text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        />
                      </div>
                    );
                  })}
                </div>
              )}

              {/* HTML preview view */}
              {view === "html" && (
                <div
                  className="border rounded-lg p-4 text-sm prose max-w-none bg-white"
                  dangerouslySetInnerHTML={{ __html: current.html_body }}
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
          <p className="text-xs text-gray-400">
            {Object.keys(overrides[activeStep] || {}).length > 0
              ? "⚠️ You have unsaved changes — click Apply changes to regenerate"
              : "Edit the blocks above to customize this email"}
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-lg hover:bg-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
