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
  importProductsPDF,
  downloadTemplate,
  getDistributorCatalogs,
  getDistributorCatalog,
  createDistributorCatalog,
  addProductToCatalog,
  removeProductFromCatalog,
  deleteDistributorCatalog,
  createProduct,
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
    setImporting(true);
    setImportResult(null);
    try {
      const result =
        importType === "csv"
          ? await importProductsCSV(importFile)
          : await importProductsPDF(importFile);
      setImportResult(result);
      if (result.created > 0 || result.updated > 0) loadProducts();
    } catch (e) {
      console.error("Erreur import:", e);
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
    try {
      const data = await getDistributorCatalog(id);
      setSelectedCatalog(data);
    } catch (e) {
      console.error("Erreur chargement catalogue:", e);
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

  const companyName = (id: number) =>
    companies.find((c) => c.id === id)?.name ?? `Company #${id}`;

  // Produits pas encore dans le catalogue sélectionné
  const productsInCatalog = new Set(
    selectedCatalog?.items?.map((i: DistributorCatalogItem) => i.product_id) ??
      [],
  );
  const availableProducts = products.filter(
    (p) => !productsInCatalog.has(p.id),
  );

  return (
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
                    setProductForm({ ...productForm, category: e.target.value })
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
                    setProductForm({ ...productForm, formats: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Prix indicatif
                </label>
                <input
                  value={productForm.indicative_price}
                  onChange={(e) =>
                    setProductForm({
                      ...productForm,
                      indicative_price: e.target.value,
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
                    <th className="pb-3">Statut</th>
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
        <div className="max-w-lg">
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setImportType("csv")}
              className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                importType === "csv"
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "border-gray-200 text-gray-600"
              }`}
            >
              CSV / Excel
            </button>
            <button
              onClick={() => setImportType("pdf")}
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

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4">
            <input
              type="file"
              accept={importType === "csv" ? ".csv,.xlsx,.xls" : ".pdf"}
              onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-gray-600"
            />
            <p className="text-xs text-gray-400 mt-2">
              {importType === "csv"
                ? "Formats acceptés : .csv, .xlsx, .xls"
                : "Format accepté : .pdf"}
            </p>
          </div>

          <button
            onClick={handleImport}
            disabled={!importFile || importing}
            className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {importing ? "Import en cours..." : "Importer"}
          </button>

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
                  Total lignes : <strong>{importResult.total_rows}</strong>
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
                      {e}
                    </p>
                  ))}
                </div>
              )}
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
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  {selectedCatalog.name}
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  {companyName(selectedCatalog.company_id)}
                </p>

                {/* Ajouter un produit */}
                <div className="flex gap-2 mb-4">
                  <select
                    value={addingProductId}
                    onChange={(e) => setAddingProductId(Number(e.target.value))}
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
                                onClick={() => handleRemoveProduct(item.id)}
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
            )}
          </div>
        </div>
      )}
    </div>
  );
}
