/**
 * SPINE V1 - catalogue API client
 * Rôle : Appels API produits + catalogue distributeurs
 * Dépendances API : /api/products, /api/distributors-catalogs
 * À faire : export produits
 */
import api from "./client";
import type {
  Product,
  DistributorCatalog,
  DistributorCatalogItem,
} from "../types";

// --- Produits ---

export const getProducts = async (): Promise<Product[]> => {
  const res = await api.get("/api/products/");
  return res.data;
};

export const importProductsCSV = async (
  file: File,
): Promise<{
  total_rows: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/products/import", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res.data;
};

export type PDFExtractedProduct = {
  item_number: string;
  name: string;
  brand?: string;
  short_description?: string;
  category?: string;
  formats?: string;
  price_range?: string;
  certifications?: string;
  segment?: string;
  confidence: number;
};

export type PDFImportPreview = {
  products: PDFExtractedProduct[];
  total_extracted: number;
  extraction_mode: "text" | "vision";
  warnings: string[];
};

export const previewProductsPDF = async (
  file: File,
): Promise<PDFImportPreview> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/products/import/pdf/preview", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const importProductsPDF = async (
  file: File,
): Promise<{
  total_rows: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/products/import/pdf", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const downloadTemplate = (): void => {
  window.open("http://localhost:8000/api/products/import/template", "_blank");
};

// --- Catalogue distributeurs ---

export const getDistributorCatalogs = async (): Promise<
  DistributorCatalog[]
> => {
  const res = await api.get("/api/distributor-catalogs/");
  return res.data;
};

export const getDistributorCatalog = async (
  id: number,
): Promise<DistributorCatalog> => {
  const res = await api.get(`/api/distributor-catalogs/${id}/`);
  return res.data;
};

export const createDistributorCatalog = async (data: {
  company_id: number;
  name: string;
  notes?: string;
}): Promise<DistributorCatalog> => {
  const res = await api.post("/api/distributor-catalogs/", data);
  return res.data;
};

export const deleteDistributorCatalog = async (id: number): Promise<void> => {
  await api.delete(`/api/distributor-catalogs/${id}/`);
};

export const addProductToCatalog = async (
  catalogId: number,
  productId: number,
  notes?: string,
): Promise<DistributorCatalogItem> => {
  const res = await api.post(`/api/distributor-catalogs/${catalogId}/items`, {
    product_id: productId,
    notes,
  });
  return res.data;
};

export const removeProductFromCatalog = async (
  catalogId: number,
  itemId: number,
): Promise<void> => {
  await api.delete(`/api/distributor-catalogs/${catalogId}/items/${itemId}`);
};

export const getProductsForCompany = async (
  companyId: number,
): Promise<{
  id: number;
  name: string;
  item_number: string;
  brand?: string;
  category?: string;
  source: "distributor_catalog" | "general_catalog";
}> => {
  const res = await api.get(
    `/api/distributor-catalogs/by-company/${companyId}/products`,
  );
  return res.data;
};

export const createProduct = async (data: {
  item_number: string;
  name: string;
  brand?: string;
  short_description?: string;
  category?: string;
  formats?: string;
  price_range?: string;
  certifications?: string;
  segment?: string;
}): Promise<Product> => {
  const res = await api.post("/api/products/", data);
  return res.data;
};

export const uploadCatalogPdf = async (
  catalogId: number,
  file: File,
): Promise<{ pdf_filename: string }> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post(
    `/api/distributor-catalogs/${catalogId}/upload-pdf`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return res.data;
};

export const getCatalogPdfBlobUrl = async (
  catalogId: number,
): Promise<string> => {
  const res = await api.get(`/api/distributor-catalogs/${catalogId}/pdf`, {
    responseType: "blob",
  });
  return URL.createObjectURL(res.data);
};
