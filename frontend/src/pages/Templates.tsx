import { useEffect, useState, useRef } from "react";
import {
  getTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
} from "../api/templates";

const CATEGORIES = ["initial", "followup_1", "followup_2", "followup_3"];

const CATEGORY_LABELS: Record<string, string> = {
  initial: "Initial",
  followup_1: "Follow-up 1",
  followup_2: "Follow-up 2",
  followup_3: "Follow-up 3",
};

const VARIABLES = [
  { label: "First Name", value: "{{prospect.first_name}}" },
  { label: "Last Name", value: "{{prospect.last_name}}" },
  { label: "Company", value: "{{prospect.company_name}}" },
  { label: "Position", value: "{{prospect.position}}" },
  { label: "Show Name", value: "{{campaign.name}}" },
  { label: "Location", value: "{{campaign.location}}" },
  { label: "Event Date", value: "{{campaign.event_date}}" },
  { label: "Distributor", value: "{{campaign.distributor_name}}" },
  { label: "My First Name", value: "{{user.first_name}}" },
  { label: "My Last Name", value: "{{user.last_name}}" },
];

type Template = {
  id?: number;
  name: string;
  category: string;
  subject_template: string;
  body_template: string;
  user_id?: number | null;
};

function Templates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Template | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const subjectRef = useRef<HTMLInputElement>(null);
  const [focusedField, setFocusedField] = useState<"subject" | "body">("body");

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } finally {
      setLoading(false);
    }
  };

  const handleNew = () => {
    setSelected({
      name: "",
      category: "initial",
      subject_template: "",
      body_template: "",
    });
    setIsNew(true);
  };

  const handleSelect = (t: Template) => {
    setSelected({ ...t });
    setIsNew(false);
  };

  const handleInsertVariable = (variable: string) => {
    if (!selected) return;

    if (focusedField === "subject" && subjectRef.current) {
      const el = subjectRef.current;
      const start = el.selectionStart ?? selected.subject_template.length;
      const end = el.selectionEnd ?? selected.subject_template.length;
      const newValue =
        selected.subject_template.slice(0, start) +
        variable +
        selected.subject_template.slice(end);
      setSelected({ ...selected, subject_template: newValue });
    } else if (focusedField === "body" && bodyRef.current) {
      const el = bodyRef.current;
      const start = el.selectionStart ?? selected.body_template.length;
      const end = el.selectionEnd ?? selected.body_template.length;
      const newValue =
        selected.body_template.slice(0, start) +
        variable +
        selected.body_template.slice(end);
      setSelected({ ...selected, body_template: newValue });
    }
  };

  const handleSave = async () => {
    if (!selected) return;
    try {
      if (isNew) {
        await createTemplate(selected);
        showMessage("success", "Template created!");
      } else if (selected.id) {
        await updateTemplate(selected.id, selected);
        showMessage("success", "Template saved!");
      }
      fetchTemplates();
      setSelected(null);
      setIsNew(false);
    } catch {
      showMessage("error", "Failed to save template");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this template?")) return;
    try {
      await deleteTemplate(id);
      showMessage("success", "Template deleted");
      if (selected?.id === id) setSelected(null);
      fetchTemplates();
    } catch {
      showMessage("error", "Failed to delete template");
    }
  };

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;

  // Group templates by category
  const grouped = CATEGORIES.reduce(
    (acc, cat) => {
      acc[cat] = templates.filter((t) => t.category === cat);
      return acc;
    },
    {} as Record<string, Template[]>,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Email Templates</h2>
        <button
          onClick={handleNew}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + New Template
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`px-4 py-3 rounded text-sm ${message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
        >
          {message.text}
        </div>
      )}

      <div className="flex gap-6">
        {/* Left — Template list */}
        <div className="w-1/3 space-y-4">
          {CATEGORIES.map((cat) => (
            <div key={cat} className="bg-white border rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-gray-700 mb-2 text-sm">
                {CATEGORY_LABELS[cat]}
              </h3>
              {grouped[cat].length === 0 ? (
                <p className="text-xs text-gray-400">No templates yet</p>
              ) : (
                <ul className="space-y-1">
                  {grouped[cat].map((t) => (
                    <li
                      key={t.id}
                      className={`flex justify-between items-center px-2 py-1 rounded cursor-pointer text-sm ${selected?.id === t.id ? "bg-blue-50 text-blue-600" : "hover:bg-gray-50"}`}
                    >
                      <span onClick={() => handleSelect(t)}>{t.name}</span>
                      {t.user_id && (
                        <button
                          onClick={() => handleDelete(t.id!)}
                          className="text-red-400 hover:text-red-600 text-xs ml-2"
                        >
                          🗑
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>

        {/* Right — Editor */}
        {selected ? (
          <div className="flex-1 bg-white border rounded-lg p-5 shadow-sm space-y-4">
            <h3 className="font-semibold text-gray-800">
              {isNew ? "New Template" : `Edit — ${selected.name}`}
            </h3>

            {/* Name + Category */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-500 mb-1">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={selected.name}
                  onChange={(e) =>
                    setSelected({ ...selected, name: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                  placeholder="Ex: My Initial Email"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">
                  Category *
                </label>
                <select
                  value={selected.category}
                  onChange={(e) =>
                    setSelected({ ...selected, category: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {CATEGORY_LABELS[c]}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Variable tags */}
            <div>
              <p className="text-xs text-gray-400 mb-2">
                Click a tag to insert at cursor position :
              </p>
              <div className="flex flex-wrap gap-2">
                {VARIABLES.map((v) => (
                  <button
                    key={v.value}
                    onClick={() => handleInsertVariable(v.value)}
                    className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded hover:bg-blue-100 border border-blue-200"
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">
                Subject *
              </label>
              <input
                ref={subjectRef}
                type="text"
                value={selected.subject_template}
                onFocus={() => setFocusedField("subject")}
                onChange={(e) =>
                  setSelected({
                    ...selected,
                    subject_template: e.target.value,
                  })
                }
                className="w-full border rounded px-3 py-2 text-sm"
                placeholder="Ex: Great meeting you at {{campaign.name}}!"
              />
            </div>

            {/* Body */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">Body *</label>
              <textarea
                ref={bodyRef}
                value={selected.body_template}
                onFocus={() => setFocusedField("body")}
                onChange={(e) =>
                  setSelected({ ...selected, body_template: e.target.value })
                }
                rows={10}
                className="w-full border rounded px-3 py-2 text-sm font-mono"
                placeholder="Hi {{prospect.first_name}}, ..."
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setSelected(null);
                  setIsNew(false);
                }}
                className="px-4 py-2 text-sm text-gray-600 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={
                  !selected.name ||
                  !selected.subject_template ||
                  !selected.body_template
                }
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                💾 Save Template
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white border rounded-lg p-5 shadow-sm flex items-center justify-center">
            <p className="text-gray-400 text-sm">
              Select a template to edit or create a new one
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Templates;
