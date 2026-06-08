/**
 * SPINE V1 - prospectImport API client
 * Role: AI-powered lead import wizard API calls
 * API: POST /api/prospects/import/ai-analyze, /import/ai-confirm
 */
import api from "./client";

export type ProductMatch = {
  product_id: number;
  product_name: string;
  item_number: string;
  confidence: number;
};

export type LeadCategory = {
  type_structure?: string;
  segment?: string;
  inferred_canal?: string;
  confidence: number;
};

export type EnrichedRow = {
  row_index: number;
  email?: string;
  first_name?: string;
  company_name?: string;
  position?: string;
  phone_number?: string;
  collateral_raw?: string;
  canal_raw?: string;
  clean_note?: string;
  product_matches: ProductMatch[];
  product_suggestions: ProductMatch[];
  category?: LeadCategory;
  original_row: Record<string, string>;
  already_exists?: boolean;
};

export type AIAnalyzeResult = {
  total_rows: number;
  column_mapping: Record<string, string | null>;
  unmapped_columns: string[];
  rows: EnrichedRow[];
};

export type AIConfirmPayload = {
  rows: EnrichedRow[];
  update_existing: boolean;
  campaign_id?: number;
};

export type AIConfirmResult = {
  success: boolean;
  created: number;
  updated: number;
  skipped: number;
  error_count: number;
  errors: string[];
  prospect_ids: number[];
};

export const aiAnalyzeImport = async (file: File): Promise<AIAnalyzeResult> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/prospects/import/ai-analyze", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res.data;
};

export const aiConfirmImport = async (
  payload: AIConfirmPayload,
): Promise<AIConfirmResult> => {
  const res = await api.post("/api/prospects/import/ai-confirm", payload);
  return res.data;
};
