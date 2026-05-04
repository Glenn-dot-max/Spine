import { useEffect, useState } from "react";
import { previewEmail } from "../api/campaigns";

type Step = 0 | 1 | 2 | 3;

const STEP_LABELS: Record<Step, string> = {
  0: "Initial",
  1: "Follow-up 1",
  2: "Follow-up 2",
  3: "Follow-up 3",
};

interface Props {
  campaignId: number;
  prospectId: number;
  prospectName: string;
  onClose: () => void;
}

export default function EmailPreviewModal({
  campaignId,
  prospectId,
  prospectName,
  onClose,
}: Props) {
  const [activeStep, setActiveStep] = useState<Step>(0);
  const [previews, setPreviews] = useState<
    Record<number, { subject: string; html_body: string } | null>
  >({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPreview(activeStep);
  }, [activeStep]);

  const loadPreview = async (step: Step) => {
    if (previews[step]) return;
    setLoading(true);
    setError(null);
    try {
      const data = await previewEmail(campaignId, prospectId, step);
      setPreviews((prev) => ({ ...prev, [step]: data }));
    } catch {
      setError("Failed to load email preview.");
    } finally {
      setLoading(false);
    }
  };

  const current = previews[activeStep];

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <div>
            <h2 className="font-semibold text-gray-800">Aperçu emails</h2>
            <p className="text-xs text-gray-500">{prospectName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            x
          </button>
        </div>

        {/* Step tabs */}
        <div className="flex gap-4 px-6 pt-4 border-b">
          {([0, 1, 2, 3] as Step[]).map((step) => (
            <button
              key={step}
              onClick={() => setActiveStep(step)}
              className={`pb-2 text-sm font-medium border-b-2 transition ${
                activeStep === step
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {STEP_LABELS[step]}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && <p className="text-sm text-gray-400">Loading...</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
          {!loading && current && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded px-4 py-2 text-sm">
                <span className="text-gray-500 font-medium">Subject:</span>
                <span className="text-gray-800">{current.subject}</span>
              </div>
              <div
                className="border rounded p-4 text-sm prose max-w-none"
                dangerouslySetInnerHTML={{ __html: current.html_body }}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded text-gray-600 hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
