/**
 * SPINE V1 — WizardCatalogueStep
 * Rôle : Onglet Catalogue embarqué dans le wizard campagne.
 *        Reproduit les 3 onglets de la page Catalogue (produits, import, catalogues dist.)
 *        directement dans le wizard, avec sélection des produits pour la campagne.
 * Props :
 *   - distributorCompanyId : pré-sélectionne le catalogue du distributeur si défini
 *   - selectedProductIds   : IDs des produits cochés pour la campagne
 *   - onSelectionChange    : callback quand la sélection change
 *   - catalogPitchText / onPitchChange : texte du pitch catalogue
 *   - offerSamples / onOfferSamplesChange / samplesNote / onSamplesNoteChange
 * Dépendances API : /api/products, /api/distributor-catalogs, /api/companies
 * À faire : —
 * Dernière modification : 2026-06-21 — création
 */
import { useState, useEffect } from "react";
import {
  getProducts,
  getProductsForCompany,
  importProductsCSV,
  previewProductsPDF,
  importPDFToCatalog,
  downloadTemplate,
  getDistributorCatalogs,
  getDistributorCatalog,
  createDistributorCatalog,
  addProductToCatalog,
  removeProductFromCatalog,
  deleteDistributorCatalog,
  uploadCatalogPdf,
  getCatalogPdfBlobUrl,
  checkPDFCredits,
  type PDFExtractedProduct,
  type PDFImportPreview,
  type PDFToCatalogResult,
  // type PDFCreditCheck,
} from "../api/catalogue";
import { getCompanies } from "../api/companies";
import type {
  Product,
  DistributorCatalog,
  DistributorCatalogItem,
} from "../types";
import type { Company } from "../types";

type CatalogProduct = {
  id: number;
  name: string;
  item_number: string;
  brand?: string;
  category?: string;
  source?: "distributor_catalog" | "general_catalog";
};

type SubTab = "products" | "import" | "catalogs";

type Props = {
  distributorCompanyId: number | null;
  distributorName: string;
  selectedProductIds: number[];
  onSelectionChange: (ids: number[]) => void;
  catalogPitchText: string;
  onPitchChange: (v: string) => void;
  offerSamples: boolean;
  onOfferSamplesChange: (v: boolean) => void;
  samplesNote: string;
  onSamplesNoteChange: (v: string) => void;
};

const CSV_TEMPLATE_REQUIRED_COLUMNS = ["item_number", "name"];
const CSV_TEMPLATE_OPTIONAL_COLUMNS = [
  "brand",
  "short_description",
  "category",
  "formats",
  "price_range",
  "certifications",
  "segments",
];

export default function WizardCatalogueStep({
  distributorCompanyId,
  distributorName,
  selectedProductIds,
  onSelectionChange,
  catalogPitchText,
  onPitchChange,
  offerSamples,
  onOfferSamplesChange,
  samplesNote,
  onSamplesNoteChange,
}: Props) {
  const [subTab, setSubTab] = useState<SubTab>("products");

  // null = choice screen | "existing" = use loaded catalogue | "import" = go to import tab
  const [catalogMode, setCatalogMode] = useState<null | "existing" | "import">(
    null,
  );

  // Which catalogue was picked in the existing flow: null = picker shown, "general" or catalog id
  const [selectedExistingCatalogId, setSelectedExistingCatalogId] = useState<
    number | "general" | null
  >(null);
  // Products from the picked distributor catalog (mapped for display)
  const [pickedCatalogProducts, setPickedCatalogProducts] = useState<
    CatalogProduct[]
  >([]);
  const [loadingPickedCatalog, setLoadingPickedCatalog] = useState(false);

  // ── Produits ──────────────────────────────────────────────────────────────
  const [catalogProducts, setCatalogProducts] = useState<CatalogProduct[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [catalogSource, setCatalogSource] = useState<"distributor" | "general">(
    "general",
  );

  // ── Import CSV/PDF ────────────────────────────────────────────────────────
  const [importType, setImportType] = useState<"csv" | "pdf">("csv");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [pdfPreviewing, setPdfPreviewing] = useState(false);
  const [pdfPreview, setPdfPreview] = useState<PDFImportPreview | null>(null);
  const [importResult, setImportResult] = useState<{
    total_rows: number;
    created: number;
    updated: number;
    skipped: number;
    errors: string[];
  } | null>(null);
  const [pdfToCatalogResult, setPdfToCatalogResult] =
    useState<PDFToCatalogResult | null>(null);
  const [pdfCreditChecking, setPdfCreditChecking] = useState(false);
  const [catalogName, setCatalogName] = useState("");
  const [catalogCompanyId, setCatalogCompanyId] = useState<number | "">("");
  const [companies, setCompanies] = useState<Company[]>([]);

  // ── Catalogues distributeurs ──────────────────────────────────────────────
  const [catalogs, setCatalogs] = useState<DistributorCatalog[]>([]);
  const [selectedCatalog, setSelectedCatalog] =
    useState<DistributorCatalog | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCatalogName, setNewCatalogName] = useState("");
  const [newCatalogCompanyId, setNewCatalogCompanyId] = useState<number | "">(
    "",
  );
  const [addingProductId, setAddingProductId] = useState<number | "">("");
  const [catalogPdfUrl, setCatalogPdfUrl] = useState<string | null>(null);
  const [pdfUploading, setPdfUploading] = useState(false);
  const [allProducts, setAllProducts] = useState<Product[]>([]);

  // ── Chargement initial ────────────────────────────────────────────────────
  useEffect(() => {
    loadCatalogProducts();
    loadCatalogs();
    loadAllProducts();
    getCompanies()
      .then(setCompanies)
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [distributorCompanyId]);

  const loadCatalogProducts = async () => {
    setLoadingCatalog(true);
    try {
      if (distributorCompanyId) {
        const data = await getProductsForCompany(distributorCompanyId);
        const products = Array.isArray(data) ? (data as CatalogProduct[]) : [];
        setCatalogProducts(products);
        setCatalogSource("distributor");
      } else {
        const data = await getProducts();
        const products: CatalogProduct[] = data.map((p) => ({
          ...p,
          source: "general_catalog" as const,
        }));
        setCatalogProducts(products);
        setCatalogSource("general");
      }
    } catch {
      setCatalogProducts([]);
    } finally {
      setLoadingCatalog(false);
    }
  };

  const loadAllProducts = async () => {
    try {
      const data = await getProducts();
      setAllProducts(data);
    } catch {
      /* silencieux */
    }
  };

  const loadCatalogs = async () => {
    try {
      const data = await getDistributorCatalogs();
      setCatalogs(data);
    } catch {
      /* silencieux */
    }
  };

  // Load a specific catalogue and auto-select all its products
  const handlePickExistingCatalog = async (id: number | "general") => {
    setSelectedExistingCatalogId(id);
    if (id === "general") {
      // General catalogue: products already loaded in catalogProducts
      onSelectionChange(catalogProducts.map((p) => p.id));
      setPickedCatalogProducts(catalogProducts);
      return;
    }
    // Distributor catalog: load full detail then map items to CatalogProduct
    setLoadingPickedCatalog(true);
    try {
      const data = await getDistributorCatalog(id);
      if (!catalogPitchText.trim() && data.notes && data.notes?.trim()) {
        onPitchChange(data.notes.trim());
      }
      const products: CatalogProduct[] = (data.items ?? []).map(
        (item: import("../types").DistributorCatalogItem) => ({
          id: item.product_id,
          name: item.product_name ?? `Product #${item.product_id}`,
          item_number: item.product_item_number ?? "",
          brand: item.product_brand,
          category: item.product_category,
          source: "distributor_catalog" as const,
        }),
      );
      setPickedCatalogProducts(products);
      onSelectionChange(products.map((p) => p.id));
    } catch {
      /* silencieux */
    } finally {
      setLoadingPickedCatalog(false);
    }
  };

  // Products currently active in the selection view
  const displayProducts =
    selectedExistingCatalogId === "general"
      ? catalogProducts
      : pickedCatalogProducts;

  const toggleProduct = (id: number) => {
    onSelectionChange(
      selectedProductIds.includes(id)
        ? selectedProductIds.filter((x) => x !== id)
        : [...selectedProductIds, id],
    );
  };

  // ── Import CSV ────────────────────────────────────────────────────────────
  const handleImport = async () => {
    if (!importFile) return;
    if (importType === "pdf") {
      // Step 1: fast credit check (no AI call)
      setPdfCreditChecking(true);
      try {
        const check = await checkPDFCredits(importFile);
        if (check.requires_confirmation) {
          const ok = window.confirm(check.warning_message);
          if (!ok) return;
        }
      } catch {
        alert(
          "Unable to estimate AI credit usage for this PDF. Please try again.",
        );
        return;
      } finally {
        setPdfCreditChecking(false);
      }

      // Step 2: AI extraction
      setPdfPreviewing(true);
      setPdfPreview(null);
      setImportResult(null);
      try {
        const preview = await previewProductsPDF(importFile);
        setPdfPreview(preview);
      } catch {
        /* silencieux */
      } finally {
        setPdfPreviewing(false);
      }
      return;
    }
    setImporting(true);
    setImportResult(null);
    try {
      const result = await importProductsCSV(importFile);
      setImportResult(result);
      if (result.created > 0 || result.updated > 0) {
        await loadCatalogProducts();
        await loadAllProducts();
      }
    } catch {
      /* silencieux */
    } finally {
      setImporting(false);
    }
  };

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
      if (
        !catalogPitchText.trim() &&
        result.generated_catalog_pitch &&
        result.generated_catalog_pitch.trim()
      ) {
        onPitchChange(result.generated_catalog_pitch.trim());
      }
      setPdfPreview(null);
      await loadCatalogProducts();
      await loadAllProducts();
      await loadCatalogs();
    } catch {
      /* silencieux */
    } finally {
      setImporting(false);
    }
  };

  // ── Catalogues distributeurs ──────────────────────────────────────────────
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
          /* PDF non dispo */
        }
      }
    } catch {
      /* silencieux */
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
    } catch {
      /* silencieux */
    } finally {
      setPdfUploading(false);
    }
  };

  const handleDeleteCatalog = async (id: number) => {
    try {
      const impact = await getDistributorCatalogDeleteImpact(id);

      const sample =
        impact.sample_product_names.length > 0
          ? `\nExemples: ${impact.sample_product_names.join(", ")}`
          : "";

      const message = [
        `⚠️ Attention, vous allez supprimer le catalogue "${impact.catalog_name}".`,
        "",
        `• ${impact.items_in_catalog} items seront retirés de ce catalogue.`,
        `• ${impact.products_only_in_this_catalog} produits seront supprimés définitivement (uniquement liés à ce catalogue).`,
        `• ${impact.products_blocked_by_usage} produits ne seront PAS supprimés (déjà utilisés).`,
        sample,
        "",
        "Confirmer la suppression ?",
      ].join("\n");

      if (!confirm(message)) return;

      await deleteDistributorCatalog(id);
      if (selectedCatalog?.id === id) setSelectedCatalog(null);
      loadCatalogs();
      loadProducts();
    } catch (e) {
      console.error("Erreur suppression catalogue:", e);
    }
  };

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

  const handleRemoveProduct = async (itemId: number) => {
    if (!selectedCatalog) return;
    try {
      await removeProductFromCatalog(selectedCatalog.id, itemId);
      const updated = await getDistributorCatalog(selectedCatalog.id);
      setSelectedCatalog(updated);
    } catch {
      /* silencieux */
    }
  };

  const productsInCatalog = new Set(
    selectedCatalog?.items?.map((i: DistributorCatalogItem) => i.product_id) ??
      [],
  );
  const availableToAdd = allProducts.filter(
    (p) => !productsInCatalog.has(p.id),
  );

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Sub-onglets */}
      <div className="flex gap-1 border-b border-gray-200 -mx-1">
        {(["products", "import", "catalogs"] as SubTab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setSubTab(t)}
            className={`px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
              subTab === t
                ? "bg-white border border-b-white border-gray-200 text-blue-600 -mb-px"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "products" && `Products (${catalogProducts.length})`}
            {t === "import" && "Import CSV / PDF"}
            {t === "catalogs" && `Distributor catalogs (${catalogs.length})`}
          </button>
        ))}
      </div>

      {/* ── ONGLET PRODUITS ── */}
      {subTab === "products" && (
        <div className="space-y-3">
          {/* ── Choice screen — shown until user picks a mode ── */}
          {catalogMode === null && (
            <>
              <p className="text-sm text-gray-500">
                How do you want to set up the catalogue for this campaign?
              </p>
              <div className="grid grid-cols-2 gap-3 pt-1">
                {/* Option A — use existing Spine catalogue */}
                <button
                  type="button"
                  onClick={() => setCatalogMode("existing")}
                  disabled={loadingCatalog}
                  className="flex flex-col items-start gap-2 p-4 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition text-left"
                >
                  <span className="text-2xl">📦</span>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">
                      Use an existing catalogue
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {loadingCatalog
                        ? "Loading..."
                        : catalogProducts.length > 0
                          ? `${catalogProducts.length} products available${
                              catalogSource === "distributor"
                                ? ` from ${distributorName}`
                                : " (general)"
                            }`
                          : "No products loaded yet"}
                    </p>
                  </div>
                </button>

                {/* Option B — import a new catalogue */}
                <button
                  type="button"
                  onClick={() => {
                    setCatalogMode("import");
                    setSubTab("import");
                  }}
                  className="flex flex-col items-start gap-2 p-4 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition text-left"
                >
                  <span className="text-2xl">📤</span>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">
                      Import a new catalogue
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      CSV, Excel or PDF — AI-powered extraction
                    </p>
                  </div>
                </button>
              </div>
            </>
          )}

          {/* ── Existing — step 1: catalogue picker ── */}
          {catalogMode === "existing" && selectedExistingCatalogId === null && (
            <>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCatalogMode(null)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  ← Back
                </button>
                <p className="text-sm text-gray-500">
                  Which catalogue do you want to use for this campaign?
                </p>
              </div>

              <div className="space-y-2">
                {/* General catalogue card */}
                <button
                  type="button"
                  onClick={() => handlePickExistingCatalog("general")}
                  disabled={loadingCatalog}
                  className="w-full flex items-center gap-3 p-3 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition text-left"
                >
                  <span className="text-xl">📦</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800">
                      General catalogue
                    </p>
                    <p className="text-xs text-gray-400">
                      {loadingCatalog
                        ? "Loading..."
                        : `${catalogProducts.length} products`}
                    </p>
                  </div>
                  <span className="text-xs text-gray-300">→</span>
                </button>

                {/* One card per distributor catalog */}
                {catalogs.length === 0 && (
                  <p className="text-xs text-gray-400 text-center py-2">
                    No distributor catalogues yet —{" "}
                    <button
                      type="button"
                      onClick={() => setSubTab("catalogs")}
                      className="underline"
                    >
                      create one
                    </button>
                  </p>
                )}
                {catalogs.map((cat) => {
                  const company = companies.find(
                    (c) => c.id === cat.company_id,
                  );
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => handlePickExistingCatalog(cat.id)}
                      className="w-full flex items-center gap-3 p-3 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition text-left"
                    >
                      <span className="text-xl">🏪</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-800">
                          {cat.name}
                        </p>
                        <p className="text-xs text-gray-400">
                          {[
                            company?.name,
                            cat.item_count != null
                              ? `${cat.item_count} products`
                              : null,
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      </div>
                      <span className="text-xs text-gray-300">→</span>
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {/* ── Existing — step 2: product selection ── */}
          {catalogMode === "existing" && selectedExistingCatalogId !== null && (
            <>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedExistingCatalogId(null);
                    onSelectionChange([]);
                  }}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  ← Change catalogue
                </button>
                <p className="text-sm text-gray-500 flex-1">
                  Select which products to highlight in this campaign.
                </p>
                <span className="text-xs px-2 py-1 rounded-full font-medium bg-blue-50 text-blue-700">
                  {selectedExistingCatalogId === "general"
                    ? "📦 General"
                    : `🏪 ${
                        catalogs.find((c) => c.id === selectedExistingCatalogId)
                          ?.name ?? "Catalog"
                      }`}
                </span>
              </div>

              {loadingPickedCatalog ? (
                <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-400">
                  Loading products...
                </div>
              ) : displayProducts.length === 0 ? (
                <div className="p-4 bg-yellow-50 border border-yellow-100 rounded-lg text-sm text-yellow-700">
                  ⚠️ No products in this catalogue.{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setCatalogMode("import");
                      setSubTab("import");
                    }}
                    className="underline font-medium"
                  >
                    Import products →
                  </button>
                </div>
              ) : (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-gray-500">
                      {selectedProductIds.length} / {displayProducts.length}{" "}
                      products selected
                    </span>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() =>
                          onSelectionChange(displayProducts.map((p) => p.id))
                        }
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Select all
                      </button>
                      <button
                        type="button"
                        onClick={() => onSelectionChange([])}
                        className="text-xs text-gray-400 hover:underline"
                      >
                        Deselect all
                      </button>
                    </div>
                  </div>
                  <div className="space-y-1 max-h-48 overflow-y-auto border rounded-lg p-1">
                    {displayProducts.map((p) => (
                      <div
                        key={p.id}
                        className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer hover:bg-gray-50 transition ${
                          selectedProductIds.includes(p.id)
                            ? "bg-blue-50/40"
                            : "opacity-50"
                        }`}
                        onClick={() => toggleProduct(p.id)}
                      >
                        <input
                          type="checkbox"
                          checked={selectedProductIds.includes(p.id)}
                          onChange={() => toggleProduct(p.id)}
                          onClick={(e) => e.stopPropagation()}
                          className="w-4 h-4 accent-blue-600 shrink-0"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">
                            {p.name}
                          </p>
                          <p className="text-xs text-gray-400">
                            {[p.item_number, p.brand, p.category]
                              .filter(Boolean)
                              .join(" · ")}
                          </p>
                        </div>
                        {p.source === "distributor_catalog" && (
                          <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded shrink-0">
                            dist.
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Pitch + samples — always visible regardless of mode */}
          <div className="border-t pt-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Catalogue pitch
              <span className="ml-2 text-xs font-normal text-gray-400">
                (leave empty for generic fallback)
              </span>
            </label>
            <textarea
              rows={3}
              placeholder="ex: Our catalogue includes premium European charcuterie..."
              value={catalogPitchText}
              onChange={(e) => onPitchChange(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="border-t pt-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                id="offer_samples"
                checked={offerSamples}
                onChange={(e) => onOfferSamplesChange(e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
              <label
                htmlFor="offer_samples"
                className="text-sm font-medium text-gray-700"
              >
                Offer product samples in the email
              </label>
            </div>
            {offerSamples && (
              <div className="mt-2">
                <textarea
                  rows={2}
                  placeholder="ex: Just send us your shipping address and we'll get samples out within 48h."
                  value={samplesNote}
                  onChange={(e) => onSamplesNoteChange(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── ONGLET IMPORT ── */}
      {subTab === "import" && (
        <div className="space-y-4">
          {/* Toggle CSV / PDF */}
          <div className="flex gap-3">
            {(["csv", "pdf"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => {
                  setImportType(t);
                  setPdfPreview(null);
                  setImportResult(null);
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                  importType === t
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-600"
                }`}
              >
                {t === "csv" ? "CSV / Excel" : "PDF catalogue"}
              </button>
            ))}
          </div>

          {importType === "csv" && (
            <div className="space-y-3">
              <button
                type="button"
                onClick={downloadTemplate}
                className="text-sm text-blue-600 underline"
              >
                ↓ Download Excel template
              </button>

              <div className="p-3 border border-gray-200 rounded-lg bg-gray-50">
                <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
                  CSV template columns
                </p>

                <div className="mb-2">
                  <p className="text-xs text-gray-500 mb-1">Required</p>
                  <div className="flex flex-wrap gap-1.5">
                    {CSV_TEMPLATE_REQUIRED_COLUMNS.map((col) => (
                      <span
                        key={col}
                        className="px-2 py-0.5 rounded bg-red-50 text-red-700 text-xs font-mono"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-500 mb-1">
                    Optional (recommended)
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {CSV_TEMPLATE_OPTIONAL_COLUMNS.map((col) => (
                      <span
                        key={col}
                        className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-mono"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="text-[11px] text-gray-400 mt-2">
                  Header example:
                  item_number,name,brand,short_description,category,formats,price_range,certifications,segments
                </p>
              </div>
            </div>
          )}
          {importType === "pdf" && (
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                🤖 The catalogue will be analysed by{" "}
                <strong>Claude Haiku Vision</strong> — automatic extraction of
                all visible products.
              </div>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                ⚠️ For large PDFs/flyers (20+ pages), AI extraction may miss
                part of the catalogue. For complete and reliable import, prefer
                the CSV / Excel template.
              </div>
            </div>
          )}

          {/* Zone upload */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept={importType === "csv" ? ".csv,.xlsx,.xls" : ".pdf"}
              onChange={(e) => {
                setImportFile(e.target.files?.[0] ?? null);
                setPdfPreview(null);
                setImportResult(null);
                setPdfToCatalogResult(null);
                setPdfCreditChecking(false);
              }}
              className="w-full text-sm text-gray-600"
            />
            <p className="text-xs text-gray-400 mt-2">
              {importType === "csv"
                ? "Formats: .csv, .xlsx, .xls"
                : "Format: .pdf"}
            </p>
          </div>

          {!pdfPreview && (
            <button
              type="button"
              onClick={handleImport}
              disabled={
                !importFile || importing || pdfPreviewing || pdfCreditChecking
              }
              className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {pdfCreditChecking
                ? "⏳ Checking cost..."
                : pdfPreviewing
                  ? "⏳ Analysing..."
                  : importType === "pdf"
                    ? "🔍 Analyze with AI"
                    : importing
                      ? "Importing..."
                      : "Import"}
            </button>
          )}

          {/* Preview PDF */}
          {pdfPreview && !importResult && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {pdfPreview.total_extracted} product
                    {pdfPreview.total_extracted > 1 ? "s" : ""} detected
                  </p>
                  <p className="text-xs text-gray-400">
                    Mode:{" "}
                    {pdfPreview.extraction_mode === "vision"
                      ? "👁 Vision AI"
                      : "📝 Text"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setPdfPreview(null)}
                  className="text-xs text-gray-400 underline"
                >
                  ✕ Restart
                </button>
              </div>

              {pdfPreview.warnings.length > 0 && (
                <div className="p-3 bg-yellow-50 rounded-lg space-y-1">
                  {pdfPreview.warnings.map((w, i) => (
                    <p key={i} className="text-xs text-yellow-700">
                      {w}
                    </p>
                  ))}
                </div>
              )}

              <div className="border rounded-lg overflow-hidden">
                <div className="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Extracted products preview
                </div>
                <div className="overflow-x-auto max-h-48 overflow-y-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-white border-b sticky top-0">
                      <tr>
                        {["Ref", "Name", "Brand", "Category", "Confidence"].map(
                          (h) => (
                            <th
                              key={h}
                              className="text-left px-3 py-2 text-gray-500 font-medium"
                            >
                              {h}
                            </th>
                          ),
                        )}
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

              <div className="space-y-2">
                <input
                  type="text"
                  value={catalogName}
                  onChange={(e) => setCatalogName(e.target.value)}
                  placeholder={
                    importFile?.name.replace(".pdf", "") ?? "Catalog name"
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
                <select
                  value={catalogCompanyId}
                  onChange={(e) =>
                    setCatalogCompanyId(
                      e.target.value ? Number(e.target.value) : "",
                    )
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">No distributor (general catalog)</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                onClick={handlePDFConfirmImport}
                disabled={importing}
                className="w-full py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {importing
                  ? "Creating catalog..."
                  : `✅ Create catalog and import (${pdfPreview.total_extracted} products)`}
              </button>
            </div>
          )}

          {/* Résultat PDF */}
          {pdfToCatalogResult && (
            <div className="p-4 rounded-lg bg-green-50 border border-green-200 text-sm space-y-1">
              <p className="font-semibold text-green-800">
                ✅ Catalog created!
              </p>
              <p className="text-gray-700">
                Catalog: <strong>{pdfToCatalogResult.catalog_name}</strong>
              </p>
              <p className="text-gray-700">
                Products created:{" "}
                <strong className="text-green-700">
                  {pdfToCatalogResult.products_created}
                </strong>
              </p>
              <p className="text-gray-700">
                Skipped (already exist):{" "}
                <strong>{pdfToCatalogResult.products_skipped}</strong>
              </p>
              <div className="flex gap-3 mt-2">
                <button
                  type="button"
                  onClick={() => {
                    setPdfToCatalogResult(null);
                    setImportFile(null);
                    setCatalogName("");
                    setSubTab("products");
                  }}
                  className="text-xs text-blue-600 underline"
                >
                  → Back to product selection
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPdfToCatalogResult(null);
                    setImportFile(null);
                    setCatalogName("");
                  }}
                  className="text-xs text-gray-400 underline"
                >
                  Import another file
                </button>
              </div>
            </div>
          )}

          {/* Résultat CSV */}
          {importResult && (
            <div
              className={`p-4 rounded-lg text-sm ${importResult.errors.length > 0 ? "bg-yellow-50 border border-yellow-200" : "bg-green-50 border border-green-200"}`}
            >
              <p className="font-medium mb-2">Import result</p>
              <p className="text-gray-700">
                Total: <strong>{importResult.total_rows}</strong>
              </p>
              <p className="text-gray-700">
                Created:{" "}
                <strong className="text-green-700">
                  {importResult.created}
                </strong>
              </p>
              <p className="text-gray-700">
                Updated:{" "}
                <strong className="text-blue-700">
                  {importResult.updated}
                </strong>
              </p>
              <p className="text-gray-700">
                Skipped: <strong>{importResult.skipped}</strong>
              </p>
              {importResult.errors.length > 0 &&
                importResult.errors.map((e, i) => (
                  <p key={i} className="text-xs text-yellow-700 mt-1">
                    {String(e)}
                  </p>
                ))}
              <div className="flex gap-3 mt-2">
                <button
                  type="button"
                  onClick={() => {
                    setImportResult(null);
                    setImportFile(null);
                    setSubTab("products");
                  }}
                  className="text-xs text-blue-600 underline"
                >
                  → Back to product selection
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── ONGLET CATALOGUES DISTRIBUTEURS ── */}
      {subTab === "catalogs" && (
        <div className="flex gap-4">
          {/* Liste */}
          <div className="w-56 flex-shrink-0 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs font-semibold text-gray-600">
                Catalogs
              </span>
              <button
                type="button"
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                + New
              </button>
            </div>

            {showCreateForm && (
              <div className="p-2 bg-gray-50 rounded-lg border space-y-2">
                <input
                  type="text"
                  placeholder="Catalog name"
                  value={newCatalogName}
                  onChange={(e) => setNewCatalogName(e.target.value)}
                  className="w-full text-xs border rounded px-2 py-1.5"
                />
                <select
                  value={newCatalogCompanyId}
                  onChange={(e) =>
                    setNewCatalogCompanyId(
                      e.target.value ? Number(e.target.value) : "",
                    )
                  }
                  className="w-full text-xs border rounded px-2 py-1.5"
                >
                  <option value="">— Select company —</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={handleCreateCatalog}
                    disabled={!newCatalogName || !newCatalogCompanyId}
                    className="flex-1 text-xs py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    Create
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="text-xs py-1 px-2 border rounded hover:bg-gray-100"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {catalogs.length === 0 ? (
              <p className="text-xs text-gray-400">
                No distributor catalog yet.
              </p>
            ) : (
              catalogs.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleOpenCatalog(c.id)}
                  className={`p-2 rounded-lg cursor-pointer text-xs border transition ${
                    selectedCatalog?.id === c.id
                      ? "border-blue-400 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300 bg-white"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-800">{c.name}</p>
                      <p className="text-gray-400">
                        {c.item_count ?? 0} products
                      </p>
                      {c.has_pdf && (
                        <p className="text-green-600">📄 PDF attached</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteCatalog(c.id);
                      }}
                      className="text-red-400 hover:text-red-600 ml-1"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Détail catalogue */}
          {selectedCatalog ? (
            <div className="flex-1 space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-semibold text-gray-800">
                  {selectedCatalog.name}
                </h3>
              </div>

              {/* Ajouter un produit */}
              <div className="flex gap-2">
                <select
                  value={addingProductId}
                  onChange={(e) =>
                    setAddingProductId(
                      e.target.value ? Number(e.target.value) : "",
                    )
                  }
                  className="flex-1 text-xs border rounded px-2 py-1.5"
                >
                  <option value="">— Add a product —</option>
                  {availableToAdd.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.item_number})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleAddProduct}
                  disabled={!addingProductId}
                  className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-40"
                >
                  Add
                </button>
              </div>

              {/* Liste produits */}
              {!selectedCatalog.items || selectedCatalog.items.length === 0 ? (
                <p className="text-xs text-gray-400">
                  No products in this catalog yet.
                </p>
              ) : (
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {selectedCatalog.items.map((item: DistributorCatalogItem) => (
                    <div
                      key={item.id}
                      className="flex justify-between items-center p-2 bg-gray-50 rounded text-xs"
                    >
                      <div>
                        <span className="font-medium text-gray-800">
                          {item.product_name}
                        </span>
                        {item.product_brand && (
                          <span className="ml-2 text-gray-400">
                            {item.product_brand}
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveProduct(item.id)}
                        className="text-red-400 hover:text-red-600"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload PDF */}
              <div className="border-t pt-2">
                <p className="text-xs font-medium text-gray-600 mb-1">
                  {selectedCatalog.has_pdf
                    ? "📄 PDF attached — replace:"
                    : "Attach a PDF:"}
                </p>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleUploadCatalogPdf(f);
                  }}
                  className="text-xs text-gray-600"
                />
                {pdfUploading && (
                  <p className="text-xs text-blue-500 mt-1">Uploading...</p>
                )}
                {catalogPdfUrl && (
                  <a
                    href={catalogPdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-600 underline mt-1 block"
                  >
                    View PDF →
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-xs text-gray-400">
              Select a catalog to manage it
            </div>
          )}
        </div>
      )}
    </div>
  );
}
