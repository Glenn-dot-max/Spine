import { useEffect, useState, useRef, use } from "react";
import {
  getTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
} from "../api/template";

const CATEGORIES = [
  "initial",
  "followup_1",
  "followup_2",
  "followup_3",
] as const;
type Category = (typeof CATEGORIES)[number];

const CATEGORY_LABELS: Record<Category, string> = {
  initial: "Initial Email",
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

const DEFAULT_TEMPLATES: Record<
  Category,
  { subject_template: string; body_template: string }
> = {
  initial: {
    subject_template: "Great meeting you at {{campaign.name}}!",
    body_template:
      "Hi {{prospect.first_name}},\n\nIt was great meeting you at {{campaign.name}} in {{campaign.location}}!\n\nI wanted to follow up on our conversation about {{prospect.company_name}}.\n\nWould you be available for a quick call this week?\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_1: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nI wanted to follow up on my previous email regarding {{campaign.name}}.\n\nDid you get a chance to review our discussion?\n\nLooking forward to hearing from you!\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_2: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nJust checking in one more time about {{campaign.name}}.\n\nI'd love to connect and explore how we can help {{prospect.company_name}}.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
  followup_3: {
    subject_template: "Re: Great meeting you at {{campaign.name}}",
    body_template:
      "Hi {{prospect.first_name}},\n\nThis will be my last follow-up regarding our meeting at {{campaign.name}}.\n\nIf the timing isn't right, no worries at all — feel free to reach out whenever you're ready.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}",
  },
};

type Template = {
  id?: number;
  name: string;
  category: string;
  subject_template: string;
  body_template: string;
  user_id?: number | null;
};

// ============================================================
// UTILS
// ============================================================
const textToHTML = (text: string): string =>
  text
    .split(/({{[^}]+}})/g)
    .map((part) => {
      if (part.match(/^{{.*}}$/)) {
        const inner = part.slice(2, -2);
        return `<span contenteditable="false" data-var="${part}" style="display:inline-block;background:#dbeafe;color:#2563eb;border:1px solid #bfdbfe;padding:1px 6px;border-radius:4px;font-size:0.75rem;font-weight:500;margin:0 2px;vertical-align:middle;cursor:default">${inner}</span>`;
      }
      return part
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .split("\n")
        .join("<br>");
    })
    .join("");

const htmlToText = (node: Node): string => {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent ?? "";
  const el = node as HTMLElement;
  if (el.getAttribute?.("data-var")) return el.getAttribute("data-var")!;
  if (el.tagName === "BR") return "\n";
  const children = Array.from(node.childNodes).map(htmlToText).join("");
  if (el.tagName === "DIV") return "\n" + children;
  return children;
};

const insertChip = (
  variable: string,
  containerRef: React.RefObject<HTMLDivElement>,
  savedRange: Range | null,
): { text: string; newRange: Range } | null => {
  const el = containerRef.current;
  if (!el) return null;

  el.focus();
  const sel = window.getSelection();
  const range =
    savedRange ??
    (() => {
      const r = document.createRange();
      r.selectNodeContents(el);
      r.collapse(false);
      return r;
    })();

  sel?.removeAllRanges();
  sel?.addRange(range);

  const chip = document.createElement("span");
  chip.contentEditable = "false";
  chip.setAttribute("data-var", variable);
  chip.style.cssText =
    "display:inline-block;background:#dbeafe;color:#2563eb;border:1px solid #bfdbfe;padding:1px 6px;border-radius:4px;font-size:0.75rem;font-weight:500;margin:0 2px;vertical-align:middle;cursor:default";
  chip.textContent = variable.slice(2, -2);

  range.deleteContents();
  range.insertNode(chip);

  const spacer = document.createTextNode("\u200B");
  range.setStartAfter(chip);
  range.insertNode(spacer);
  range.setStartAfter(spacer);
  range.collapse(true);

  sel?.removeAllRanges();
  sel?.addRange(range);

  const text = Array.from(el.childNodes).map(htmlToText).join("");
  return { text, newRange: range.cloneRange() };
};

// ============================================================
// RICH BODY EDITOR
// ============================================================
function RichBodyEditor({
  value,
  onChange,
  onBlur,
  onSaveSelection,
  isDefault,
  divRef,
}: {
  value: string;
  onChange: (val: string) => void;
  onBlur: () => void;
  onSaveSelection: (r: Range) => void;
  isDefault: boolean;
  divRef: React.RefObject<HTMLDivElement>;
}) {
  const prevValueRef = useRef("");

  useEffect(() => {
    if (!divRef.current) return;
    divRef.current.innerHTML = textToHTML(value);
    prevValueRef.current = value;
    divRef.current.focus();
    const range = document.createRange();
    range.selectNodeContents(divRef.current);
    range.collapse(false);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(range);
  }, []);

  useEffect(() => {
    if (
      prevValueRef.current !== value &&
      divRef.current &&
      document.activeElement !== divRef.current
    ) {
      divRef.current.innerHTML = textToHTML(value);
      prevValueRef.current = value;
    }
  }, [value]);

  const saveSelection = () => {
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0 && divRef.current?.contains(sel.anchorNode)) {
      onSaveSelection(sel.getRangeAt(0).cloneRange());
    }
  };

  const handleInput = () => {
    if (!divRef.current) return;
    const text = Array.from(divRef.current.childNodes).map(htmlToText).join("");
    prevValueRef.current = text;
    onChange(text);
    saveSelection();
  };

  return (
    <div
      ref={divRef}
      contentEditable
      suppressContentEditableWarning
      onInput={handleInput}
      onKeyUp={saveSelection}
      onMouseUp={saveSelection}
      onBlur={onBlur}
      className={`w-full border-2 border-blue-400 rounded px-3 py-2 text-sm min-h-[200px] leading-relaxed outline-none ${
        isDefault ? "text-gray-400 italic" : ""
      }`}
    />
  );
}

// ============================================================
// MAIN COMPONENT
// ============================================================
function Templates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Template | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [isWizard, setIsWizard] = useState(false);
  const [editingBody, setEditingBody] = useState(false);
  const [isDefault, setIsDefault] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [focusedField, setFocusedField] = useState<"subject" | "body">("body");

  const subjectEditorRef = useRef<HTMLDivElement>(null);
  const bodyEditorRef = useRef<HTMLDivElement>(null);
  const savedBodySelectionRef = useRef<Range | null>(null);
  const savedSubjectSelectionRef = useRef<Range | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (subjectEditorRef.current) {
      subjectEditorRef.current.innerHTML = textToHTML(
        selected?.subject_template ?? "",
      );
    }
  }, [selected?.subject_template]);

  const fetchTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } finally {
      setLoading(false);
    }
  };

  const startWizard = () => {
    const cat = CATEGORIES[0];
    setWizardStep(0);
    setIsWizard(true);
    setIsNew(true);
    setIsDefault(true);
    setEditingBody(false);
    setSelected({
      name: "",
      category: cat,
      subject_template: DEFAULT_TEMPLATES[cat].subject_template,
      body_template: DEFAULT_TEMPLATES[cat].body_template,
    });
  };

  const handleSelect = (t: Template) => {
    setSelected({ ...t });
    setIsNew(false);
    setIsWizard(false);
    setIsDefault(false);
    setEditingBody(false);
  };

  const handleInsertVariable = (variable: string) => {
    if (!selected) return;

    if (focusedField === "subject") {
      const result = insertChip(
        variable,
        subjectEditorRef,
        savedSubjectSelectionRef.current,
      );
      if (result) {
        savedSubjectSelectionRef.current = result.newRange;
        setSelected({ ...selected, subject_template: result.text });
        setIsDefault(false);
      }
    } else if (focusedField === "body" && editingBody) {
      const result = insertChip(
        variable,
        bodyEditorRef,
        savedBodySelectionRef.current,
      );
      if (result) {
        savedBodySelectionRef.current = result.newRange;
        setSelected({ ...selected, body_template: result.text });
        setIsDefault(false);
      }
    }
  };

  const clearDefault = () => {
    if (!selected) return;
    setSelected({ ...selected, subject_template: "", body_template: "" });
    setIsDefault(false);
  };

  const handleSave = async () => {
    if (!selected) return;
    try {
      const savedName = isWizard
        ? `${selected.name} - ${CATEGORY_LABELS[selected.category as Category]}`
        : selected.name;

      const payload = { ...selected, name: savedName };

      if (isNew) {
        await createTemplate(payload);
      } else if (selected.id) {
        await updateTemplate(selected.id, payload);
      }
      await fetchTemplates();

      if (isWizard && wizardStep < 3) {
        const nextStep = wizardStep + 1;
        const nextCat = CATEGORIES[nextStep];
        setWizardStep(nextStep);
        setIsDefault(true);
        setEditingBody(false);
        setSelected({
          name: selected.name,
          category: nextCat,
          subject_template: DEFAULT_TEMPLATES[nextCat].subject_template,
          body_template: DEFAULT_TEMPLATES[nextCat].body_template,
        });
        showMessage(
          "success",
          `${CATEGORY_LABELS[CATEGORIES[wizardStep]]} saved! Now edit ${CATEGORY_LABELS[nextCat]}.`,
        );
      } else {
        showMessage("success", isNew ? "Template created!" : "Template saved!");
        setSelected(null);
        setIsNew(false);
        setIsWizard(false);
        setWizardStep(0);
        setEditingBody(false);
      }
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
          onClick={startWizard}
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
                      className={`flex justify-between items-center px-2 py-1 rounded cursor-pointer text-sm ${
                        selected?.id === t.id
                          ? "bg-blue-50 text-blue-600"
                          : "hover:bg-gray-50"
                      }`}
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
            {/* Wizard progress bar */}
            {isWizard && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-500">
                  {CATEGORIES.map((cat, i) => (
                    <span
                      key={cat}
                      className={`font-medium ${
                        i === wizardStep
                          ? "text-blue-600"
                          : i < wizardStep
                            ? "text-green-600"
                            : "text-gray-400"
                      }`}
                    >
                      {i < wizardStep ? "✓ " : ""}
                      {CATEGORY_LABELS[cat]}
                    </span>
                  ))}
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full transition-all"
                    style={{ width: `${((wizardStep + 1) / 4) * 100}%` }}
                  />
                </div>
              </div>
            )}

            <h3 className="font-semibold text-gray-800">
              {isWizard
                ? `Step ${wizardStep + 1}/4 — ${CATEGORY_LABELS[CATEGORIES[wizardStep]]}`
                : `Edit — ${selected.name}`}
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
                  onChange={(e) => {
                    setSelected({ ...selected, name: e.target.value });
                    setIsDefault(false);
                  }}
                  className="w-full border rounded px-3 py-2 text-sm"
                  placeholder="Ex: My Initial Email"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">
                  Category
                </label>
                <input
                  type="text"
                  value={
                    CATEGORY_LABELS[selected.category as Category] ??
                    selected.category
                  }
                  disabled
                  className="w-full border rounded px-3 py-2 text-sm bg-gray-50 text-gray-500"
                />
              </div>
            </div>

            {/* Variable tags */}
            <div>
              <p className="text-xs text-gray-400 mb-2">
                Click a tag to insert at cursor position:
              </p>
              <div className="flex flex-wrap gap-2">
                {VARIABLES.map((v) => (
                  <button
                    key={v.value}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleInsertVariable(v.value);
                    }}
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
              <div
                ref={subjectEditorRef}
                contentEditable
                suppressContentEditableWarning
                onFocus={() => setFocusedField("subject")}
                onKeyUp={() => {
                  const sel = window.getSelection();
                  if (
                    sel &&
                    sel.rangeCount > 0 &&
                    subjectEditorRef.current?.contains(sel.anchorNode)
                  ) {
                    savedSubjectSelectionRef.current = sel
                      .getRangeAt(0)
                      .cloneRange();
                  }
                }}
                onMouseUp={() => {
                  const sel = window.getSelection();
                  if (
                    sel &&
                    sel.rangeCount > 0 &&
                    subjectEditorRef.current?.contains(sel.anchorNode)
                  ) {
                    savedSubjectSelectionRef.current = sel
                      .getRangeAt(0)
                      .cloneRange();
                  }
                }}
                onBlur={(e) => {
                  const text = Array.from(e.currentTarget.childNodes)
                    .map(htmlToText)
                    .join("");
                  setSelected({ ...selected, subject_template: text });
                }}
                onInput={(e) => {
                  const text = Array.from(e.currentTarget.childNodes)
                    .map(htmlToText)
                    .join("");
                  setSelected((prev) =>
                    prev ? { ...prev, subject_template: text } : prev,
                  );
                }}
                className={`w-full border rounded px-3 py-2 text-sm outline-none focus:border-2 focus:border-blue-400 min-h-[38px] leading-relaxed ${
                  isDefault ? "text-gray-400 italic" : ""
                }`}
              />
            </div>

            {/* Body */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-sm text-gray-500">Body *</label>
                <div className="flex gap-2 items-center">
                  {isDefault && (
                    <button
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={clearDefault}
                      className="text-xs text-red-400 hover:text-red-600 border border-red-200 px-2 py-0.5 rounded"
                    >
                      🗑 Clear suggestion
                    </button>
                  )}
                  {editingBody ? (
                    <span className="text-xs text-blue-400 italic">
                      Click outside to preview
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400 italic">
                      Click to edit
                    </span>
                  )}
                </div>
              </div>

              {editingBody ? (
                <RichBodyEditor
                  value={selected.body_template}
                  onChange={(val) => {
                    setSelected((prev) =>
                      prev ? { ...prev, body_template: val } : prev,
                    );
                    setIsDefault(false);
                  }}
                  onBlur={() => setEditingBody(false)}
                  onSaveSelection={(r) => {
                    savedBodySelectionRef.current = r;
                  }}
                  isDefault={isDefault}
                  divRef={bodyEditorRef}
                />
              ) : (
                <div
                  onClick={() => {
                    setEditingBody(true);
                    setFocusedField("body");
                  }}
                  className={`w-full border rounded px-3 py-2 text-sm bg-white min-h-[200px] whitespace-pre-wrap leading-relaxed cursor-text hover:border-blue-300 transition-colors ${
                    isDefault ? "text-gray-400 italic" : ""
                  }`}
                >
                  {selected.body_template ? (
                    selected.body_template
                      .split(/({{[^}]+}})/g)
                      .map((part, i) =>
                        part.match(/^{{.*}}$/) ? (
                          <span
                            key={i}
                            className="inline-block bg-blue-100 text-blue-600 border border-blue-200 px-1.5 py-0.5 rounded text-xs font-medium mx-0.5 align-middle"
                          >
                            {part.slice(2, -2)}
                          </span>
                        ) : (
                          <span key={i}>{part}</span>
                        ),
                      )
                  ) : (
                    <span className="text-gray-300">
                      Click to write your email body...
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setSelected(null);
                  setIsNew(false);
                  setIsWizard(false);
                  setWizardStep(0);
                  setEditingBody(false);
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
                {isWizard && wizardStep < 3
                  ? "Save & Next →"
                  : "💾 Save Template"}
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
