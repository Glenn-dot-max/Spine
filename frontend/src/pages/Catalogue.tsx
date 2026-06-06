/**
 * SPINE V1 - Catalogue
 * Rôle : gestion du catalogue produits général + catalogues par distributeur
 * Props : aucune (page autonome)
 * Dépendances API: /api/products, /api/distributors-catalogs, api/companies
 * À faire : export produits, pagination
 */
import React, { useEffect, useState } from "react";
import {
  getProducts,
  importProductsCSV,
  previewProductsPDF,
  importPDFToCatalog,
  type PDFExtractedProduct,
  type PDFImportPreview,
  type PDFToCatalogResult,
  downloadTemplate,
  getDistributorCatalogs,
  getDistributorCatalog,
  createDistributorCatalog,
  addProductToCatalog,
  removeProductFromCatalog,
  deleteDistributorCatalog,
  createProduct,
  deleteProduct,
  updateProduct,
  uploadCatalogPdf,
  getCatalogPdfBlobUrl,
  getProductCatalogMemberships,
  type CatalogMembership,
  type CatalogMemberships,
} from "../api/catalogue";

import { getCompanies } from "../api/companies";
import type {
  Product,
  DistributorCatalog,
  DistributorCatalogItem,
} from "../types";
import type { Company } from "../types";

type Tab = "products" | "import" | "distributors";

export default function Catalogue() {
  const [activeTab, setActiveTab] = useState<Tab>("products");

  // -- Produits --
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    brand: "",
    category: "",
    formats: "",
    price_range: "",
    short_description: "",
  });
  const [catalogMemberships, setCatalogMemberships] =
    useState<CatalogMemberships>({});
  const [productForm, setProductForm] = useState({
    item_number: "",
    name: "",
    brand: "",
    category: "",
    formats: "",
    price_range: "",
    short_description: "",
  });

  // -- Imports --
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importType, setImportType] = useState<"csv" | "pdf">("csv");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    total_rows: number;
    created: number;
    updated: number;
    skipped: number;
    errors: string[];
  } | null>(null);
  const [pdfPreview, setPdfPreview] = useState<PDFImportPreview | null>(null);
  const [pdfPreviewing, setPdfPreviewing] = useState(false);
  const [catalogName, setCatalogName] = useState("");
  const [catalogCompanyId, setCatalogCompanyId] = useState<number | "">("");
  const [pdfToCatalogResult, setPdfToCatalogResult] =
    useState<PDFToCatalogResult | null>(null);

  // -- Catalogues distributeurs --
  const [catalogs, setCatalogs] = useState<DistributorCatalog[]>([]);
  const [selectedCatalog, setSelectedCatalog] =
    useState<DistributorCatalog | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCatalogName, setNewCatalogName] = useState("");
  const [newCatalogCompanyId, setNewCatalogCompanyId] = useState<number | "">(
    "",
  );
  const [addingProductId, setAddingProductId] = useState<number | "">("");
  const [catalogPdfUrl, setCatalogPdfUrl] = useState<string | null>(null);
  const [pdfUploading, setPdfUploading] = useState(false);

  // Chargement initial
  useEffect(() => {
    loadProducts();
    loadCatalogs();
    loadCompanies();
  }, []);

  const loadProducts = async () => {
    setLoadingProducts(true);
    try {
      const data = await getProducts();
      setProducts(data);
      const memberships = await getProductCatalogMemberships();
      setCatalogMemberships(memberships);
    } catch (e) {
      console.error("Erreur chargement produits:", e);
    } finally {
      setLoadingProducts(false);
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProduct({
        ...productForm,
        brand: productForm.brand || undefined,
        category: productForm.category || undefined,
        formats: productForm.formats || undefined,
        price_range: productForm.price_range || undefined,
        short_description: productForm.short_description || undefined,
      });
      setShowProductForm(false);
      setProductForm({
        item_number: "",
        name: "",
        brand: "",
        category: "",
        formats: "",
        price_range: "",
        short_description: "",
      });
      loadProducts();
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail || "Erreur création produit");
    }
  };

  const handleDeleteProduct = async (id: number, name: string) => {
    if (!confirm(`Supprimer "${name}" ? Cette action est irréversible.`))
      return;
    try {
      await deleteProduct(id);
      loadProducts();
    } catch (e) {
      console.error("Erreur suppression produit:", e);
    }
  };

  const handleEditProduct = (p: Product) => {
    setEditingProduct(p);
    setEditForm({
      name: p.name,
      brand: p.brand ?? "",
      category: p.category ?? "",
      formats: p.formats ?? "",
      price_range: p.price_range ?? "",
      short_description: p.short_description ?? "",
    });
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    try {
      await updateProduct(editingProduct.id, {
        name: editForm.name || undefined,
        brand: editForm.brand || undefined,
        category: editForm.category || undefined,
        formats: editForm.formats || undefined,
        price_range: editForm.price_range || undefined,
        short_description: editForm.short_description || undefined,
      });
      setEditingProduct(null);
      loadProducts();
    } catch (e) {
      console.error("Erreur mise à jour produit:", e);
    }
  };

  const loadCatalogs = async () => {
    try {
      const data = await getDistributorCatalogs();
      setCatalogs(data);
    } catch (e) {
      console.error("Erreur chargement catalogues:", e);
    }
  };

  const loadCompanies = async () => {
    try {
      const data = await getCompanies();
      setCompanies(data);
    } catch (e) {
      console.error("Erreur chargement entreprises:", e);
    }
  };

  // -- import CSV/PDF --
  const handleImport = async () => {
    if (!importFile) return;
    if (importType === "pdf") {
      setPdfPreviewing(true);
      setPdfPreview(null);
      setImportResult(null);
      try {
        const preview = await previewProductsPDF(importFile);
        setPdfPreview(preview);
      } catch (e) {
        console.error("Erreur preview PDF:", e);
      } finally {
        setPdfPreviewing(false);
      }
      return;
    }
    // CSV : import direct
    setImporting(true);
    setImportResult(null);
    try {
      const result = await importProductsCSV(importFile);
      setImportResult(result);
      if (result.created > 0 || result.updated > 0) loadProducts();
    } catch (e) {
      console.error("Erreur import:", e);
    } finally {
      setImporting(false);
    }
  };

  // -- import PDF : confirmation après preview --
  const handlePDFConfirmImport = async () => {
    if (!importFile) return;
    setImporting(true);
    setPdfToCatalogResult(null);
    try {
      const name = catalogName.trim() || importFile.name.replace(".pdf", "");
      const result = await importPDFToCatalog(
        importFile,
        name,
        catalogCompanyId ? Number(catalogCompanyId) : undefined,
      );
      setPdfToCatalogResult(result);
      setPdfPreview(null);
      loadProducts();
      loadCatalogs();
    } catch (e) {
      console.error("Erreur import PDF vers catalogue:", e);
    } finally {
      setImporting(false);
    }
  };

  // -- Créer un catalogue --
  const handleCreateCatalog = async () => {
    if (!newCatalogName || !newCatalogCompanyId) return;
    try {
      await createDistributorCatalog({
        company_id: Number(newCatalogCompanyId),
        name: newCatalogName,
      });
      setShowCreateForm(false);
      setNewCatalogName("");
      setNewCatalogCompanyId("");
      loadCatalogs();
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail || "Erreur création catalogue");
    }
  };

  // -- Ouvrir un catalogue --
  const handleOpenCatalog = async (id: number) => {
    setCatalogPdfUrl(null);
    try {
      const data = await getDistributorCatalog(id);
      setSelectedCatalog(data);
      if (data.has_pdf) {
        try {
          const url = await getCatalogPdfBlobUrl(id);
          setCatalogPdfUrl(url);
        } catch {
          // PDF non disponible, on ignore
        }
      }
    } catch (e) {
      console.error("Erreur chargement catalogue:", e);
    }
  };

  const handleUploadCatalogPdf = async (file: File) => {
    if (!selectedCatalog) return;
    setPdfUploading(true);
    try {
      await uploadCatalogPdf(selectedCatalog.id, file);
      const url = await getCatalogPdfBlobUrl(selectedCatalog.id);
      setCatalogPdfUrl(url);
      const updated = await getDistributorCatalog(selectedCatalog.id);
      setSelectedCatalog(updated);
      loadCatalogs();
    } catch (e) {
      console.error("Erreur upload PDF:", e);
    } finally {
      setPdfUploading(false);
    }
  };

  // -- Supprimer un catalogue --
  const handleDeleteCatalog = async (id: number) => {
    if (!confirm("Supprimer ce catalogue ?")) return;
    try {
      await deleteDistributorCatalog(id);
      if (selectedCatalog?.id === id) setSelectedCatalog(null);
      loadCatalogs();
    } catch (e) {
      console.error("Erreur suppression catalogue:", e);
    }
  };

  // -- Ajouter un produit au catalogue --
  const handleAddProduct = async () => {
    if (!selectedCatalog || !addingProductId) return;
    try {
      await addProductToCatalog(selectedCatalog.id, Number(addingProductId));
      setAddingProductId("");
      const updated = await getDistributorCatalog(selectedCatalog.id);
      setSelectedCatalog(updated);
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail || "Erreur ajout produit");
    }
  };

  // -- Retirer un produit du catalogue --
  const handleRemoveProduct = async (itemId: number) => {
    if (!selectedCatalog) return;
    try {
      await removeProductFromCatalog(selectedCatalog.id, itemId);
      const updated = await getDistributorCatalog(selectedCatalog.id);
      setSelectedCatalog(updated);
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      console.error("Erreur retrait produit", err);
    }
  };

  const companyName = (id?: number) =>
    id ? (companies.find((c) => c.id === id)?.name ?? `Company #${id}`) : "—";

  // Produits pas encore dans le catalogue sélectionné
  const productsInCatalog = new Set(
    selectedCatalog?.items?.map((i: DistributorCatalogItem) => i.product_id) ??
      [],
  );
  const availableProducts = products.filter(
    (p) => !productsInCatalog.has(p.id),
  );

  return (
    <>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Catalogue produits
        </h1>

        {/* Onglets */}
        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {(["products", "import", "distributors"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab
                  ? "bg-white border border-b-white border-gray-200 text-blue-600 -mb-px"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "products" && `Produits (${products.length})`}
              {tab === "import" && "Import CSV / PDF"}
              {tab === "distributors" &&
                `Catalogues distributeurs (${catalogs.length})`}
            </button>
          ))}
        </div>

        {/* ===== ONGLET PRODUITS ===== */}
        {activeTab === "products" && (
          <div>
            {/* Bouton + formulaire d'ajout manuel */}
            <div className="mb-4 flex justify-end">
              <button
                onClick={() => setShowProductForm(!showProductForm)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
              >
                + Ajouter un produit
              </button>
            </div>

            {showProductForm && (
              <form
                onSubmit={handleCreateProduct}
                className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg grid grid-cols-2 gap-3"
              >
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Référence *
                  </label>
                  <input
                    required
                    value={productForm.item_number}
                    onChange={(e) =>
                      setProductForm({
                        ...productForm,
                        item_number: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Nom *
                  </label>
                  <input
                    required
                    value={productForm.name}
                    onChange={(e) =>
                      setProductForm({ ...productForm, name: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Marque
                  </label>
                  <input
                    value={productForm.brand}
                    onChange={(e) =>
                      setProductForm({ ...productForm, brand: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Catégorie
                  </label>
                  <input
                    value={productForm.category}
                    onChange={(e) =>
                      setProductForm({
                        ...productForm,
                        category: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Formats
                  </label>
                  <input
                    value={productForm.formats}
                    onChange={(e) =>
                      setProductForm({
                        ...productForm,
                        formats: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Prix indicatif
                  </label>
                  <input
                    value={productForm.price_range}
                    onChange={(e) =>
                      setProductForm({
                        ...productForm,
                        price_range: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm text-gray-600 mb-1">
                    Description courte
                  </label>
                  <textarea
                    value={productForm.short_description}
                    onChange={(e) =>
                      setProductForm({
                        ...productForm,
                        short_description: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                    rows={3}
                  />
                </div>
                <div className="col-span-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowProductForm(false)}
                    className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Créer
                  </button>
                </div>
              </form>
            )}
            {loadingProducts ? (
              <p className="text-gray-500">Chargement...</p>
            ) : products.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p className="text-lg">Aucun produit dans le catalogue</p>
                <button
                  onClick={() => setActiveTab("import")}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Importer des produits
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-gray-500">
                      <th className="pb-3 pr-4">Référence</th>
                      <th className="pb-3 pr-4">Nom</th>
                      <th className="pb-3 pr-4">Marque</th>
                      <th className="pb-3 pr-4">Catégorie</th>
                      <th className="pb-3 pr-4">Formats</th>
                      <th className="pb-3 pr-4">Statut</th>
                      <th className="pb-3 pr-4">Catalogues</th>
                      <th className="pb-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((p) => (
                      <tr
                        key={p.id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-3 pr-4 font-mono text-xs text-gray-500">
                          {p.item_number}
                        </td>
                        <td className="py-3 pr-4 font-medium text-gray-900">
                          {p.name}
                        </td>
                        <td className="py-3 pr-4 text-gray-600">
                          {p.brand ?? "—"}
                        </td>
                        <td className="py-3 pr-4 text-gray-600">
                          {p.category ?? "—"}
                        </td>
                        <td className="py-3 pr-4 text-gray-600">
                          {p.formats ?? "—"}
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              p.is_active
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-100 text-gray-500"
                            }`}
                          >
                            {p.is_active ? "Actif" : "Inactif"}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <div className="flex flex-wrap gap-1">
                            {(catalogMemberships[p.id] ?? []).length === 0 ? (
                              <span className="text-xs text-gray-300">—</span>
                            ) : (
                              (catalogMemberships[p.id] ?? []).map(
                                (m: CatalogMembership) => (
                                  <span
                                    key={m.catalog_id}
                                    className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100"
                                  >
                                    {m.catalog_name}
                                  </span>
                                ),
                              )
                            )}
                          </div>
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleEditProduct(p)}
                              className="text-xs text-blue-500 hover:text-blue-700"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeleteProduct(p.id, p.name)}
                              className="text-xs text-red-400 hover:text-red-600"
                            >
                              🗑
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ===== ONGLET IMPORT ===== */}
        {activeTab === "import" && (
          <div className="max-w-2xl">
            {/* Toggle CSV / PDF */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => {
                  setImportType("csv");
                  setPdfPreview(null);
                  setImportResult(null);
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                  importType === "csv"
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-600"
                }`}
              >
                CSV / Excel
              </button>
              <button
                onClick={() => {
                  setImportType("pdf");
                  setPdfPreview(null);
                  setImportResult(null);
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                  importType === "pdf"
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-600"
                }`}
              >
                PDF catalogue
              </button>
            </div>

            {importType === "csv" && (
              <button
                onClick={downloadTemplate}
                className="mb-4 text-sm text-blue-600 underline hover:text-blue-800"
              >
                ↓ Télécharger le template Excel
              </button>
            )}

            {importType === "pdf" && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                🤖 Le catalogue sera analysé par{" "}
                <strong>Claude Haiku Vision</strong> - extraction automatique de
                tous les produits visibles.
              </div>
            )}

            {/* Zone d'upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4">
              <input
                type="file"
                accept={importType === "csv" ? ".csv,.xlsx,.xls" : ".pdf"}
                onChange={(e) => {
                  setImportFile(e.target.files?.[0] ?? null);
                  setPdfPreview(null);
                  setImportResult(null);
                }}
                className="w-full text-sm text-gray-600"
              />
              <p className="text-xs text-gray-400 mt-2">
                {importType === "csv"
                  ? "Formats acceptés : .csv, .xlsx, .xls"
                  : "Format accepté : .pdf"}
              </p>
            </div>

            {/* Bouton principal (masqué si preview déjà affichée) */}
            {!pdfPreview && (
              <button
                onClick={handleImport}
                disabled={!importFile || importing || pdfPreviewing}
                className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {pdfPreviewing
                  ? "⏳ Analyse en cours..."
                  : importType === "pdf"
                    ? "🔍 Analyzing with AI"
                    : importing
                      ? "Import en cours..."
                      : "Importer"}
              </button>
            )}

            {/* Preview PDF - tableau avant confirmation */}
            {pdfPreview && !importResult && (
              <div className="mt-4 space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">
                      {pdfPreview.total_extracted} produit
                      {pdfPreview.total_extracted > 1 ? "s" : ""} détecté
                      {pdfPreview.total_extracted > 1 ? "s" : ""}
                    </p>
                    <p className="text-xs text-gray-400">
                      Mode :{" "}
                      {pdfPreview.extraction_mode === "vision"
                        ? "Vision AI"
                        : "📝 Texte"}
                    </p>
                  </div>
                  <button
                    onClick={() => setPdfPreview(null)}
                    className="text-xs text-gray-400 hover:text-gray-600 underline"
                  >
                    x Recommencer
                  </button>
                </div>

                {pdfPreview.warnings.length > 0 && (
                  <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg space-y-1">
                    {pdfPreview.warnings.map((w, i) => (
                      <p key={i} className="text-xs text-yellow-700">
                        {w}
                      </p>
                    ))}
                  </div>
                )}

                <div className="border rounded-lg overflow-hidden">
                  <div className="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Aperçu des produits extraits
                  </div>
                  <div className="overflow-x-auto max-h-72 overflow-y-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-white border-b sticky top-0">
                        <tr>
                          <th className="text-left px-3 py-2 text-gray-500 font-medium">
                            Référence
                          </th>
                          <th className="text-left px-3 py-2 text-gray-500 font-medium">
                            Nom
                          </th>
                          <th className="text-left px-3 py-2 text-gray-500 font-medium">
                            Marque
                          </th>
                          <th className="text-left px-3 py-2 text-gray-500 font-medium">
                            Catégorie
                          </th>
                          <th className="text-left px-3 py-2 text-gray-500 font-medium">
                            Confiance
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {pdfPreview.products.map(
                          (p: PDFExtractedProduct, i: number) => (
                            <tr
                              key={i}
                              className="border-b last:border-0 hover:bg-gray-50"
                            >
                              <td className="px-3 py-2 font-mono text-gray-500">
                                {p.item_number}
                              </td>
                              <td className="px-3 py-2 font-medium text-gray-800">
                                {p.name}
                              </td>
                              <td className="px-3 py-2 text-gray-500">
                                {p.brand ?? "-"}
                              </td>
                              <td className="px-3 py-2 text-gray-500">
                                {p.category ?? "-"}
                              </td>
                              <td className="px-3 py-2">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                                    p.confidence >= 0.8
                                      ? "bg-green-100 text-green-700"
                                      : p.confidence >= 0.5
                                        ? "bg-yellow-100 text-yellow-700"
                                        : "bg-gray-100 text-gray-700"
                                  }`}
                                >
                                  {Math.round(p.confidence * 100)}%
                                </span>
                              </td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Nom du catalogue + distributeur optionnel */}
                <div className="space-y-2">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Nom du catalogue
                    </label>
                    <input
                      type="text"
                      value={catalogName}
                      onChange={(e) => setCatalogName(e.target.value)}
                      placeholder={
                        importFile?.name.replace(".pdf", "") ?? "Mon catalogue"
                      }
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Distributeur{" "}
                      <span className="text-gray-400">(optionnel)</span>
                    </label>
                    <select
                      value={catalogCompanyId}
                      onChange={(e) =>
                        setCatalogCompanyId(
                          e.target.value ? Number(e.target.value) : "",
                        )
                      }
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    >
                      <option value="">Aucun distributeur</option>
                      {companies.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  onClick={handlePDFConfirmImport}
                  disabled={importing}
                  className="w-full py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  {importing
                    ? "Création du catalogue..."
                    : `✅ Créer le catalogue et importer (${pdfPreview.total_extracted} produits)`}
                </button>
              </div>
            )}

            {/* Résultat import PDF -> catalogue */}
            {pdfToCatalogResult && (
              <div className="mt-4 p-4 rounded-lg text-sm bg-green-50 border border-green-200">
                <p className="font-medium mb-2">
                  ✅ Catalogue créé avec succès
                </p>
                <ul className="space-y-1 text-gray-700">
                  <li>
                    Catalogue :{" "}
                    <strong>{pdfToCatalogResult.catalog_name}</strong>
                  </li>
                  <li>
                    Produits importés :{" "}
                    <strong className="text-green-700">
                      {pdfToCatalogResult.products_created}
                    </strong>
                  </li>
                  <li>
                    Ignorés (déjà existants) :{" "}
                    <strong>{pdfToCatalogResult.products_skipped}</strong>
                  </li>
                  <li>
                    PDF lié :{" "}
                    <strong>
                      {pdfToCatalogResult.pdf_attached ? "✅ Oui" : "⚠️ Non"}
                    </strong>
                  </li>
                </ul>
                <button
                  onClick={() => {
                    setPdfToCatalogResult(null);
                    setImportFile(null);
                    setCatalogName("");
                    setCatalogCompanyId("");
                    setActiveTab("distributors");
                  }}
                  className="mt-3 text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  → Voir le catalogue
                </button>
              </div>
            )}

            {/* Résultat final CSV */}
            {importResult && (
              <div
                className={`mt-4 p-4 rounded-lg text-sm ${
                  importResult.errors.length > 0
                    ? "bg-yellow-50 border border-yellow-200"
                    : "bg-green-50 border border-green-200"
                }`}
              >
                <p className="font-medium mb-2">Résultat de l'import</p>
                <ul className="space-y-1 text-gray-700">
                  <li>
                    Total : <strong>{importResult.total_rows}</strong>
                  </li>
                  <li>
                    Créés :{" "}
                    <strong className="text-green-700">
                      {importResult.created}
                    </strong>
                  </li>
                  <li>
                    Mis à jour :{" "}
                    <strong className="text-blue-700">
                      {importResult.updated}
                    </strong>
                  </li>
                  <li>
                    Ignorés : <strong>{importResult.skipped}</strong>
                  </li>
                </ul>
                {importResult.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="font-medium text-yellow-700">Erreurs :</p>
                    {importResult.errors.map((e, i) => (
                      <p key={i} className="text-xs text-yellow-700">
                        {String(e)}
                      </p>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => {
                    setImportResult(null);
                    setImportFile(null);
                  }}
                  className="mt-3 text-xs text-gray-400 hover:text-gray-600 underline"
                >
                  Importer un autre fichier
                </button>
              </div>
            )}
          </div>
        )}

        {/* ===== ONGLET CATALOGUES DISTRIBUTEURS ===== */}
        {activeTab === "distributors" && (
          <div className="flex gap-6">
            {/* Liste des catalogues */}
            <div className="w-72 flex-shrink-0">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-sm font-semibold text-gray-700">
                  Catalogues
                </h2>
                <button
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  + Nouveau
                </button>
              </div>

              {showCreateForm && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
                  <input
                    type="text"
                    placeholder="Nom du catalogue"
                    value={newCatalogName}
                    onChange={(e) => setNewCatalogName(e.target.value)}
                    className="w-full text-sm border border-gray-300 rounded px-3 py-1.5"
                  />
                  <select
                    value={newCatalogCompanyId}
                    onChange={(e) =>
                      setNewCatalogCompanyId(Number(e.target.value))
                    }
                    className="w-full text-sm border border-gray-300 rounded px-3 py-1.5"
                  >
                    <option value="">Sélectionner un distributeur</option>
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                  <div className="flex gap-2">
                    <button
                      onClick={handleCreateCatalog}
                      className="flex-1 text-xs py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Créer
                    </button>
                    <button
                      onClick={() => setShowCreateForm(false)}
                      className="flex-1 text-xs py-1.5 border border-gray-300 rounded hover:bg-gray-100"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              )}

              {catalogs.length === 0 ? (
                <p className="text-sm text-gray-400">Aucun catalogue créé</p>
              ) : (
                <ul className="space-y-1">
                  {catalogs.map((c) => (
                    <li
                      key={c.id}
                      onClick={() => handleOpenCatalog(c.id)}
                      className={`flex justify-between items-center px-3 py-2 rounded-lg cursor-pointer text-sm ${
                        selectedCatalog?.id === c.id
                          ? "bg-blue-50 text-blue-700 font-medium"
                          : "hover:bg-gray-100 text-gray-700"
                      }`}
                    >
                      <div>
                        <p className="font-medium">{c.name}</p>
                        <p className="text-xs text-gray-400">
                          {companyName(c.company_id)} · {c.item_count} produit
                          {(c.item_count ?? 0) > 1 ? "s" : ""}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCatalog(c.id);
                        }}
                        className="text-gray-300 hover:text-red-500 text-xs ml-2"
                      >
                        ✕
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Détail du catalogue sélectionné */}
            <div className="flex-1">
              {!selectedCatalog ? (
                <div className="text-center py-12 text-gray-400">
                  <p>Sélectionne un catalogue pour voir ses produits</p>
                </div>
              ) : (
                <div>
                  {/* Header catalogue */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">
                        {selectedCatalog.name}
                      </h2>
                      <p className="text-sm text-gray-500">
                        {companyName(selectedCatalog.company_id)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {catalogPdfUrl && (
                        <a
                          href={catalogPdfUrl}
                          download={
                            selectedCatalog.pdf_filename ?? "catalogue.pdf"
                          }
                          className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-1"
                        >
                          ↓ {selectedCatalog.pdf_filename ?? "catalogue.pdf"}
                        </a>
                      )}
                      <label
                        className={`text-xs px-3 py-1.5 rounded-lg cursor-pointer flex items-center gap-1 ${pdfUploading ? "opacity-50 cursor-not-allowed" : "bg-blue-50 text-blue-600 hover:bg-blue-100"}`}
                      >
                        📎{" "}
                        {pdfUploading
                          ? "Upload..."
                          : selectedCatalog.has_pdf
                            ? "Remplacer le PDF"
                            : "Joindre un PDF"}
                        <input
                          type="file"
                          accept=".pdf"
                          className="hidden"
                          disabled={pdfUploading}
                          onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (f) handleUploadCatalogPdf(f);
                          }}
                        />
                      </label>
                    </div>
                  </div>

                  {/* Layout 2 colonnes : produits + PDF  */}
                  <div
                    className={`flex gap-4 ${catalogPdfUrl ? "items-start" : ""}`}
                  >
                    <div className="flex-1 min-w-0">
                      {/* Ajouter un produit */}
                      <div className="flex gap-2 mb-4">
                        <select
                          value={addingProductId}
                          onChange={(e) =>
                            setAddingProductId(Number(e.target.value))
                          }
                          className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2"
                        >
                          <option value="">Ajouter un produit...</option>
                          {availableProducts.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.item_number} — {p.name}{" "}
                              {p.brand ? `(${p.brand})` : ""}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={handleAddProduct}
                          disabled={!addingProductId}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                        >
                          Ajouter
                        </button>
                      </div>

                      {/* Liste des produits dans ce catalogue */}
                      {!selectedCatalog.items ||
                      selectedCatalog.items.length === 0 ? (
                        <p className="text-sm text-gray-400">
                          Aucun produit dans ce catalogue
                        </p>
                      ) : (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-gray-200 text-left text-gray-500">
                              <th className="pb-2 pr-4">Référence</th>
                              <th className="pb-2 pr-4">Nom</th>
                              <th className="pb-2 pr-4">Marque</th>
                              <th className="pb-2 pr-4">Catégorie</th>
                              <th className="pb-2"></th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedCatalog.items.map(
                              (item: DistributorCatalogItem) => (
                                <tr
                                  key={item.id}
                                  className="border-b border-gray-100 hover:bg-gray-50"
                                >
                                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">
                                    {item.product_item_number}
                                  </td>
                                  <td className="py-2 pr-4 font-medium text-gray-900">
                                    {item.product_name}
                                  </td>
                                  <td className="py-2 pr-4 text-gray-600">
                                    {item.product_brand ?? "—"}
                                  </td>
                                  <td className="py-2 pr-4 text-gray-600">
                                    {item.product_category ?? "—"}
                                  </td>
                                  <td className="py-2 text-right">
                                    <button
                                      onClick={() =>
                                        handleRemoveProduct(item.id)
                                      }
                                      className="text-xs text-gray-400 hover:text-red-500"
                                    >
                                      Retirer
                                    </button>
                                  </td>
                                </tr>
                              ),
                            )}
                          </tbody>
                        </table>
                      )}
                    </div>

                    {/* Preview PDF inline */}
                    {catalogPdfUrl && (
                      <div className="w-[480px] flex-shrink-0">
                        <div className="flex justify-between items-center mb-1">
                          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
                            Aperçu du catalogue
                          </p>
                          <a
                            href={catalogPdfUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-500 hover:text-blue-700"
                          >
                            ↗ Ouvrir en plein écran
                          </a>
                        </div>
                        <iframe
                          src={`${catalogPdfUrl}#toolbar=1&navpanes=1&scrollbar=1&view=FitH`}
                          className="w-full rounded-lg border border-gray-200"
                          style={{
                            height: "calc(100vh - 280px)",
                            minHeight: "500px",
                          }}
                          title="Catalogue PDF"
                        ></iframe>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal édition produit */}
      {editingProduct && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-800">
                Modifier — {editingProduct.item_number}
              </h3>
              <button
                onClick={() => setEditingProduct(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <form
              onSubmit={handleUpdateProduct}
              className="grid grid-cols-2 gap-3"
            >
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Nom *
                </label>
                <input
                  required
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Marque
                </label>
                <input
                  value={editForm.brand}
                  onChange={(e) =>
                    setEditForm({ ...editForm, brand: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Catégorie
                </label>
                <input
                  value={editForm.category}
                  onChange={(e) =>
                    setEditForm({ ...editForm, category: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Formats
                </label>
                <input
                  value={editForm.formats}
                  onChange={(e) =>
                    setEditForm({ ...editForm, formats: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Prix
                </label>
                <input
                  value={editForm.price_range}
                  onChange={(e) =>
                    setEditForm({ ...editForm, price_range: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Description
                </label>
                <textarea
                  value={editForm.short_description}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      short_description: e.target.value,
                    })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  rows={2}
                />
              </div>
              <div className="col-span-2 flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setEditingProduct(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
