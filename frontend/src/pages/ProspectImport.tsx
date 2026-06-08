/**
 * SPINE V1 — ProspectImport
 * Role: AI-powered lead import wizard (3 steps)
 * Step 1: Upload file
 * Step 2: Review AI mapping + enrichments (editable)
 * Step 3: Confirm import with options
 * API: /api/prospects/import/ai-analyze, /import/ai-confirm
 * Todo: chunking for large files (> 50 rows)
 */
import React, { useEffect, useState } from "react";
import {
  aiAnalyzeImport,
  aiConfirmImport,
  type AIAnalyzeResult,
  type EnrichedRow,
  type ProductMatch,
} from "../api/prospectImport";
import { getCampaigns } from "../api/campaigns";
import type { Campaign } from "../types";

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

type Step = 1 | 2 | 3;

export default function ProspectImport() {
  const [step, setStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AIAnalyzeResult | null>(null);
  const [rows, setRows] = useState<EnrichedRow[]>([]);
  const [columnMapping, setColumnMapping] = useState<
    Record<string, string | null>
  >({});
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  // Step 3 options
  const [updateExisting, setUpdateExisting] = useState(false);
  const [campaignId, setCampaignId] = useState<number | "">("");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    created: number;
    updated: number;
    skipped: number;
    errors: string[];
  } | null>(null);

  useEffect(() => {
    getCampaigns().then(setCampaigns).catch(console.error);
  }, []);

  // -- Step 1: Analyze --
  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    try {
      const res = await aiAnalyzeImport(file);
      setResult(res);
      setRows(res.rows);
      setColumnMapping(res.column_mapping);
      setStep(2);
    } catch (e) {
      console.error("Analysis error:", e);
      alert("Error analyzing file. Check the console.");
    } finally {
      setAnalyzing(false);
    }
  };

  // -- Step 2: Edit mapping --
  const updateMapping = (original: string, newField: string | null) => {
    setColumnMapping((prev) => ({ ...prev, [original]: newField }));
  };

  // -- Step 2: Toggle product match --
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
        } else {
          return {
            ...r,
            product_matches: r.product_matches.filter(
              (m: ProductMatch) => m.product_id !== match.product_id,
            ),
          };
        }
      }),
    );
  };

  // -- Step 2: Edit note --
  const updateNote = (rowIndex: number, note: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.row_index === rowIndex ? { ...r, clean_note: note } : r,
      ),
    );
  };

  // -- Step 3: Confirm import --
  const handleConfirm = async () => {
    setImporting(true);
    try {
      const res = await aiConfirmImport({
        rows,
        update_existing: updateExisting,
        campaign_id: campaignId ? Number(campaignId) : undefined,
      });
      setImportResult({
        created: res.created,
        updated: res.updated,
        skipped: res.skipped,
        errors: res.errors,
      });
      setStep(3);
    } catch (e) {
      console.error("Import error:", e);
      alert("Import failed. Check the console.");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">AI Lead Import</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm">
        {[
          { n: 1, label: "Upload" },
          { n: 2, label: "Review" },
          { n: 3, label: "Done" },
        ].map(({ n, label }) => (
          <React.Fragment key={n}>
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                step === n
                  ? "bg-blue-600 text-white"
                  : step > n
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-400"
              }`}
            >
              {step > n ? "✓" : n} {label}
            </div>
            {n < 3 && <div className="w-6 h-px bg-gray-200" />}
          </React.Fragment>
        ))}
      </div>

      {/* ===== STEP 1: UPLOAD ===== */}
      {step === 1 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <div>
            <h2 className="font-semibold text-gray-800 mb-1">
              Upload your lead file
            </h2>
            <p className="text-sm text-gray-500">
              Supports CSV, XLSX, XLS — any column format from any trade show
              export. AI will automatically map your columns to Spine fields.
            </p>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.tsv,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-gray-600"
            />
            <p className="text-xs text-gray-400 mt-2">CSV, XLSX, XLS, TSV</p>
          </div>

          <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
            🤖 <strong>Claude Haiku</strong> will map your columns, match
            products from your catalog, rewrite notes as professional CRM
            entries, and infer lead categories — all before you confirm the
            import.
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!file || analyzing}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? "⏳ Analyzing with AI..." : "🔍 Analyze with AI"}
          </button>
        </div>
      )}

      {/* ===== STEP 2: REVIEW ===== */}
      {step === 2 && result && (
        <div className="space-y-6">
          {/* Column mapping review */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex justify-between items-center mb-3">
              <h2 className="font-semibold text-gray-800">Column Mapping</h2>
              {result.unmapped_columns.length > 0 && (
                <span className="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">
                  {result.unmapped_columns.length} unrecognized column(s)
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(columnMapping).map(([original, mapped]) => (
                <div key={original} className="flex items-center gap-2 text-sm">
                  <span className="flex-1 truncate text-gray-600 font-mono text-xs bg-gray-50 px-2 py-1 rounded">
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

          {/* Leads preview */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex justify-between items-center mb-3">
              <h2 className="font-semibold text-gray-800">
                {result.total_rows} lead{result.total_rows > 1 ? "s" : ""}{" "}
                detected
              </h2>
              <p className="text-xs text-gray-400">
                Click a row to review enrichments
              </p>
            </div>

            <div className="space-y-2">
              {rows.map((row) => (
                <div
                  key={row.row_index}
                  className="border border-gray-100 rounded-lg overflow-hidden"
                >
                  {/* Row summary */}
                  <div
                    className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-gray-50 ${
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

                    {/* Category badges */}
                    <div className="flex gap-1 flex-shrink-0">
                      {row.category?.type_structure && (
                        <span
                          className={`px-1.5 py-0.5 rounded text-xs font-medium ${CONFIDENCE_BADGE(row.category.confidence)}`}
                        >
                          {row.category.type_structure}
                        </span>
                      )}
                      {row.category?.segment && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-600">
                          {row.category.segment}
                        </span>
                      )}
                      {row.product_matches.length > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-600">
                          {row.product_matches.length} product
                          {row.product_matches.length > 1 ? "s" : ""}
                        </span>
                      )}
                    </div>

                    <span className="text-gray-300 text-xs">
                      {expandedRow === row.row_index ? "▲" : "▼"}
                    </span>
                  </div>

                  {/* Expanded detail */}
                  {expandedRow === row.row_index && (
                    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 space-y-3">
                      {/* CRM Note */}
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          CRM Note (AI rewritten)
                        </label>
                        <textarea
                          value={row.clean_note ?? ""}
                          onChange={(e) =>
                            updateNote(row.row_index, e.target.value)
                          }
                          className="w-full text-sm border border-gray-200 rounded px-3 py-2 bg-white"
                          rows={2}
                        />
                      </div>

                      {/* Product matches */}
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
          <div className="flex justify-between">
            <button
              onClick={() => {
                setStep(1);
                setResult(null);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              ← Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Review done → Import options
            </button>
          </div>
        </div>
      )}

      {/* ===== STEP 3: CONFIRM ===== */}
      {step === 3 && !importResult && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">Import Options</h2>

          <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
            Ready to import <strong>{rows.length} leads</strong>.
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={updateExisting}
              onChange={(e) => setUpdateExisting(e.target.checked)}
              className="rounded"
            />
            Update existing leads if email already exists
          </label>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Add to campaign <span className="text-gray-400">(optional)</span>
            </label>
            <select
              value={campaignId}
              onChange={(e) =>
                setCampaignId(e.target.value ? Number(e.target.value) : "")
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">No campaign</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              ← Back to review
            </button>
            <button
              onClick={handleConfirm}
              disabled={importing}
              className="px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {importing
                ? "Importing..."
                : `✅ Confirm import (${rows.length} leads)`}
            </button>
          </div>
        </div>
      )}

      {/* ===== DONE ===== */}
      {step === 3 && importResult && (
        <div className="bg-white border border-green-200 rounded-xl p-6 space-y-3">
          <h2 className="font-semibold text-green-700">✅ Import complete</h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-700">
                {importResult.created}
              </p>
              <p className="text-xs text-gray-500">Created</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">
                {importResult.updated}
              </p>
              <p className="text-xs text-gray-500">Updated</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-500">
                {importResult.skipped}
              </p>
              <p className="text-xs text-gray-500">Skipped</p>
            </div>
          </div>
          {importResult.errors.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
              <p className="text-xs font-medium text-yellow-700 mb-1">
                {importResult.errors.length} error(s):
              </p>
              {importResult.errors.map((e, i) => (
                <p key={i} className="text-xs text-yellow-600">
                  {e}
                </p>
              ))}
            </div>
          )}
          <button
            onClick={() => {
              setStep(1);
              setFile(null);
              setResult(null);
              setRows([]);
              setImportResult(null);
            }}
            className="text-sm text-blue-600 hover:underline"
          >
            Import another file
          </button>
        </div>
      )}
    </div>
  );
}
