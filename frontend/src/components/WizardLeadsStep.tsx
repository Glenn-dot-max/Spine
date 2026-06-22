/**
 * SPINE V1 — WizardLeadsStep
 * Rôle : Import leads IA embarqué dans le wizard campagne.
 *        Sub-steps 1 (upload + analyse Haiku) et 2 (review mapping + enrichissements).
 *        La confirmation finale (aiConfirmImport) est déléguée au wizard parent
 *        au moment de créer la campagne, avec le campaign_id fraîchement créé.
 * Props :
 *   - onRowsReady    : callback quand l'user valide le review → passe les rows enrichies
 *   - readyRowCount  : nb de leads déjà stagés (affiche résumé si > 0)
 * Dépendances API : /api/prospects/import/ai-analyze
 * À faire : chunking pour fichiers > 50 lignes
 * Dernière modification : 2026-06-22 — création
 */
import React, { useState } from "react";
import {
  aiAnalyzeImport,
  type AIAnalyzeResult,
  type EnrichedRow,
  type ProductMatch,
} from "../api/prospectImport";

const SPINE_FIELDS = [
  { value: "email", label: "Email" },
  { value: "first_name", label: "First Name" },
  { value: "last_name", label: "Last Name" },
  { value: "company_name", label: "Company" },
  { value: "position", label: "Position" },
  { value: "phone_number", label: "Phone" },
  { value: "source_notes", label: "Notes" },
  { value: "canal", label: "Canal" },
  { value: "product_interest", label: "Product Interest" },
];

const CONFIDENCE_BADGE = (c: number) => {
  if (c >= 0.75) return "bg-green-100 text-green-700";
  if (c >= 0.5) return "bg-yellow-100 text-yellow-700";
  return "bg-gray-100 text-gray-500";
};

type Props = {
  onRowsReady: (rows: EnrichedRow[]) => void;
  readyRowCount: number;
};

export default function WizardLeadsStep({ onRowsReady, readyRowCount }: Props) {
  const [subStep, setSubStep] = useState<1 | 2>(1);
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AIAnalyzeResult | null>(null);
  const [rows, setRows] = useState<EnrichedRow[]>([]);
  const [columnMapping, setColumnMapping] = useState<
    Record<string, string | null>
  >({});
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [analyzeError, setAnalyzeError] = useState("");
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualForm, setManualForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    company_name: "",
    position: "",
    clean_note: "",
  });
  const [manualRows, setManualRows] = useState<EnrichedRow[]>([]);

  const handleAddManual = () => {
    if (!manualForm.email) return;
    const newRow: EnrichedRow = {
      row_index: -(manualRows.length + 1), // index négatif = saisie manuelle
      first_name: manualForm.first_name,
      last_name: manualForm.last_name,
      email: manualForm.email,
      company_name: manualForm.company_name,
      position: manualForm.position,
      clean_note: manualForm.clean_note,
      product_matches: [],
      product_suggestions: [],
      original_row: {},
    };
    const updated = [...manualRows, newRow];
    setManualRows(updated);
    setManualForm({
      first_name: "",
      last_name: "",
      email: "",
      company_name: "",
      position: "",
      clean_note: "",
    });
    // Stage immediately si pas d'import fichier en cours
    if (!result) onRowsReady(updated);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    setAnalyzeError("");
    try {
      const res = await aiAnalyzeImport(file);
      setResult(res);
      setRows(res.rows);
      setColumnMapping(res.column_mapping);
      setSubStep(2);
    } catch {
      setAnalyzeError(
        "Error analyzing file — check that the file has an email column.",
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const updateMapping = (original: string, newField: string | null) => {
    setColumnMapping((prev) => ({ ...prev, [original]: newField }));
  };

  const toggleProductMatch = (
    rowIndex: number,
    match: ProductMatch,
    add: boolean,
  ) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.row_index !== rowIndex) return r;
        if (add) {
          return {
            ...r,
            product_matches: [...r.product_matches, match],
            product_suggestions: r.product_suggestions.filter(
              (s: ProductMatch) => s.product_id !== match.product_id,
            ),
          };
        }
        return {
          ...r,
          product_matches: r.product_matches.filter(
            (m: ProductMatch) => m.product_id !== match.product_id,
          ),
        };
      }),
    );
  };

  const updateNote = (rowIndex: number, note: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.row_index === rowIndex ? { ...r, clean_note: note } : r,
      ),
    );
  };

  return (
    <div className="space-y-4">
      {/* Indicateur sous-steps */}
      <div className="flex items-center gap-2 text-xs">
        {(
          [
            { n: 1, label: "Upload" },
            { n: 2, label: "Review" },
          ] as const
        ).map(({ n, label }) => (
          <React.Fragment key={n}>
            <div
              className={`px-3 py-1 rounded-full font-medium ${
                subStep === n
                  ? "bg-blue-600 text-white"
                  : subStep > n
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-400"
              }`}
            >
              {subStep > n ? "✓" : n} {label}
            </div>
            {n < 2 && <div className="w-4 h-px bg-gray-200" />}
          </React.Fragment>
        ))}
      </div>

      {/* ── SUB-STEP 1 : UPLOAD ── */}
      {subStep === 1 && (
        <div className="space-y-3">
          {/* Sucess badge - visible as soon as leads are staged */}
          {readyRowCount > 0 && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <span className="text-lg">✅</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-green-700">
                  {readyRowCount} lead{readyRowCount > 1 ? "s" : ""} staged for
                  import
                </p>
                <p className="text-xs text-green-500">
                  Add more below, or click Next to continue.
                </p>
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500">
            Upload your leads file from the trade show. Claude Haiku will map
            columns, match products and rewrite notes as CRM entries.
          </p>

          <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center">
            <p className="text-3xl mb-2">📋</p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.tsv"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setAnalyzeError("");
              }}
              className="w-full text-sm text-gray-600"
            />
            <p className="text-xs text-gray-400 mt-2">
              CSV, XLSX, XLS — any column format
            </p>
          </div>

          <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
            🤖 <strong>Claude Haiku</strong> will map your columns, match
            products from your catalog, rewrite notes as professional CRM
            entries, and infer lead categories.
          </div>

          {analyzeError && (
            <div className="p-3 bg-red-50 rounded-lg text-sm text-red-700">
              ❌ {analyzeError}
            </div>
          )}

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!file || analyzing}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? "⏳ Analyzing with AI..." : "🔍 Analyze with AI"}
          </button>

          {/* Separator */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400">or</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Manual entry */}
          {manualRows.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-xs font-medium text-green-700">
                ✅ {manualRows.length} lead{manualRows.length > 1 ? "s" : ""}{" "}
                added manually
              </p>
            </div>
          )}

          {showManualForm ? (
            <div className="border border-gray-200 rounded-xl p-4 space-y-3 bg-gray-50">
              <p className="text-sm font-medium text-gray-700">
                Add a lead manually
              </p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    First name
                  </label>
                  <input
                    type="text"
                    value={manualForm.first_name}
                    onChange={(e) =>
                      setManualForm((f) => ({
                        ...f,
                        first_name: e.target.value,
                      }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    placeholder="Jane"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Last name
                  </label>
                  <input
                    type="text"
                    value={manualForm.last_name}
                    onChange={(e) =>
                      setManualForm((f) => ({
                        ...f,
                        last_name: e.target.value,
                      }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    placeholder="Smith"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={manualForm.email}
                    onChange={(e) =>
                      setManualForm((f) => ({ ...f, email: e.target.value }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    placeholder="jane.smith@company.com"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Company
                  </label>
                  <input
                    type="text"
                    value={manualForm.company_name}
                    onChange={(e) =>
                      setManualForm((f) => ({
                        ...f,
                        company_name: e.target.value,
                      }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    placeholder="Sysco"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Position
                  </label>
                  <input
                    type="text"
                    value={manualForm.position}
                    onChange={(e) =>
                      setManualForm((f) => ({ ...f, position: e.target.value }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    placeholder="Buyer"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">
                    Note
                  </label>
                  <textarea
                    value={manualForm.clean_note}
                    onChange={(e) =>
                      setManualForm((f) => ({
                        ...f,
                        clean_note: e.target.value,
                      }))
                    }
                    className="w-full border rounded px-2 py-1.5 text-sm resize-none"
                    rows={2}
                    placeholder="Met at booth #42, interested in..."
                  />
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowManualForm(false)}
                  className="px-3 py-1.5 border rounded-lg text-sm text-gray-600 hover:bg-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddManual}
                  disabled={!manualForm.email}
                  className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  + Add lead
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowManualForm(true)}
              className="w-full py-2 border border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition"
            >
              + Add a lead manually
            </button>
          )}
        </div>
      )}

      {/* ── SUB-STEP 2 : REVIEW ── */}
      {subStep === 2 && result && (
        <div className="space-y-3">
          {/* Column mapping */}
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-gray-700">
                Column Mapping
              </span>
              {result.unmapped_columns.length > 0 && (
                <span className="text-xs text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded-full">
                  {result.unmapped_columns.length} unrecognized
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(columnMapping).map(([original, mapped]) => (
                <div
                  key={original}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <span className="flex-1 truncate text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">
                    {original}
                  </span>
                  <span className="text-gray-300">→</span>
                  <select
                    value={mapped ?? ""}
                    onChange={(e) =>
                      updateMapping(original, e.target.value || null)
                    }
                    className={`flex-1 text-xs border rounded px-2 py-1 ${
                      mapped
                        ? "border-green-200 bg-green-50"
                        : "border-gray-200"
                    }`}
                  >
                    <option value="">— ignore —</option>
                    {SPINE_FIELDS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* Liste leads */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-gray-800">
                {result.total_rows} lead{result.total_rows > 1 ? "s" : ""}{" "}
                detected
              </span>
              <span className="text-xs text-gray-400">Click a row to edit</span>
            </div>
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {rows.map((row) => (
                <div
                  key={row.row_index}
                  className="border border-gray-100 rounded-lg overflow-hidden"
                >
                  <div
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50 ${
                      row.already_exists ? "bg-yellow-50" : ""
                    }`}
                    onClick={() =>
                      setExpandedRow(
                        expandedRow === row.row_index ? null : row.row_index,
                      )
                    }
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {row.first_name} {row.last_name}
                        {row.already_exists && (
                          <span className="ml-2 text-xs text-yellow-600">
                            existing
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {row.email} · {row.company_name ?? "—"}
                      </p>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {row.category?.type_structure && (
                        <span
                          className={`px-1.5 py-0.5 rounded text-xs font-medium ${CONFIDENCE_BADGE(row.category.confidence)}`}
                        >
                          {row.category.type_structure}
                        </span>
                      )}
                      {row.product_matches.length > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-600">
                          {row.product_matches.length}p
                        </span>
                      )}
                    </div>
                    <span className="text-gray-300 text-xs">
                      {expandedRow === row.row_index ? "▲" : "▼"}
                    </span>
                  </div>

                  {expandedRow === row.row_index && (
                    <div className="px-3 py-2 bg-gray-50 border-t border-gray-100 space-y-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          CRM Note (AI rewritten)
                        </label>
                        <textarea
                          value={row.clean_note ?? ""}
                          onChange={(e) =>
                            updateNote(row.row_index, e.target.value)
                          }
                          className="w-full text-xs border border-gray-200 rounded px-2 py-1.5 bg-white"
                          rows={2}
                        />
                      </div>
                      {(row.product_matches.length > 0 ||
                        row.product_suggestions.length > 0) && (
                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">
                            Product Interest — {row.collateral_raw ?? "—"}
                          </label>
                          <div className="flex flex-wrap gap-1">
                            {row.product_matches.map((m: ProductMatch) => (
                              <span
                                key={m.product_id}
                                className="flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded text-xs"
                              >
                                ✓ {m.product_name}
                                <button
                                  type="button"
                                  onClick={() =>
                                    toggleProductMatch(row.row_index, m, false)
                                  }
                                  className="text-green-400 hover:text-red-500 ml-1"
                                >
                                  ✕
                                </button>
                              </span>
                            ))}
                            {row.product_suggestions.map((m: ProductMatch) => (
                              <span
                                key={m.product_id}
                                className="flex items-center gap-1 px-2 py-0.5 bg-yellow-50 text-yellow-700 border border-yellow-200 rounded text-xs"
                              >
                                ? {m.product_name} (
                                {Math.round(m.confidence * 100)}%)
                                <button
                                  type="button"
                                  onClick={() =>
                                    toggleProductMatch(row.row_index, m, true)
                                  }
                                  className="text-yellow-500 hover:text-green-600 ml-1"
                                >
                                  ✓
                                </button>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-1">
            <button
              type="button"
              onClick={() => {
                setSubStep(1);
                setResult(null);
              }}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={() => onRowsReady(rows)}
              className="px-5 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              ✅ Stage {rows.length} leads for import
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
