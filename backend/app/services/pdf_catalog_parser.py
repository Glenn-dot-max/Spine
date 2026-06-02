"""
SPINE V1 - PDF Catalog Parser
==========================
Rôle : Extraction automatique de produits depuis un catalogue PDF
Dépendances : pdfplumber
Utilisé par : services/product_import.py
Sécurité : Fichier supprimé après extraction - pas de stockage permanent.
A faire : Améliorer la précision de l'extraction (tâche 9)
Dernière modification : 2024-06-02 - Création initiale
"""
import pdfplumber
import re
import io
from typing import List, Dict

def parse_pdf_catalog(file_bytes: bytes) -> List[Dict]:
    """
    Extrait les produits d'un catalogue PDF.
    
    Stratégie :
    1. Cherche des tableaux structurés (pdfplumber table detection)
    2. Fallback : extraction ligne par ligne avec regex

    Returns:
        List de dicts avec les champs produit détectés
    """
    products = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Stratégie 1 : tableaux détectés automatiquement
            tables = page.extract_tables()
            for table in tables:
                extracted = _parse_table(table)
                products.extend(extracted)
            
            # Stratégie 2 : si aucun tableau, parse le texte ligne par ligne
            if not tables:
                text = page.extract_text()
                if text:
                    extracted = _parse_text_lines(text)
                    products.extend(extracted)
          
    # Dédoublonnage par item_number
    seen = set()
    unique_products = []
    for p in products:
        key = p.get('item_number', '').strip()
        if key and key not in seen:
            seen.add(key)
            unique_products.append(p)

    return unique_products

def _parse_table(table: List[List]) -> List[Dict]:
    """
    Parse un tableau extrait par pdfplumber.
    Détecte les colonnes automatiquement depuis la première ligne (header).
    """
    if not table or len(table) < 2:
        return []
    
    # première ligne = headers
    raw_headers = [str(h).lower().strip() if h else '' for h in table[0]]
    
    # Mapping des noms de colonnes courants
    COLUMN_MAP = {
        'item': 'item_number',
        'item#': 'item_number',
        'item number': 'item_number',
        'sku': 'item_number',
        'code': 'item_number',
        'ref': 'item_number',
        'reference': 'item_number',
        'product': 'name',
        'product name': 'name',
        'description': 'name',
        'name': 'name',
        'brand': 'brand',
        'marque': 'brand',
        'format': 'formats',
        'formats': 'formats',
        'size': 'formats',
        'pack size': 'formats',
        'price': 'price_range',
        'unit price': 'price_range',
        'msrp': 'price_range',
        'category': 'category',
        'segment': 'segments',
        'certification': 'certifications',
        'cert': 'certifications',
    }

    headers = [COLUMN_MAP.get(h, h) for h in raw_headers]

    products = []
    for row in table[1:]:
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue
        
        product = {}
        for i, cell in enumerate(row):
            if i < len(headers) and headers[i] in COLUMN_MAP.values():
                if cell and str(cell).strip():
                    product[headers[i]] = str(cell).strip()

        # Un product valide doit avoir au minimum un nom ou un item_number
        if product.get('name') or product.get('item_number'):
            # Si pas d'item_number, on génère un depuis le nom
            if not product.get('item_number') and product.get('name'):
                product['item_number'] = _generate_item_number(product['name'])
            products.append(product)
    
    return products 

def _parse_text_lines(text: str) -> List[Dict]:
    """
    Fallback : parse le texte brut ligne par ligne.
    Détecte les patterns courants : "SKU - Nom du produit - Format"
    """
    products = []
    lines = text.split('\n')

    # Pattern : commence par un code alphanumérique (SKU)
    sku_pattern = re.compile(r'^\s*([A-Za-z0-9\-]+)\s*[-:]\s*(.+)$')

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        match = sku_pattern.match(line)
        if match:
            item_number = match.group(1).strip()
            rest = match.group(2).strip()

            # Essaie de séparer nom et description par un tiret ou pipe
            parts = re.split(r'\s{2,}|\||-{2,}', rest, maxsplit=1)
            name = parts[0].strip()
            short_description = parts[1].strip() if len(parts) > 1 else None

            if name:
                products.append({
                    'item_number': item_number,
                    'name': name,
                    'short_description': short_description
                })

    return products

def _generate_item_number(name: str) -> str:
    """génère un item_number depuis un nom si absent."""
    clean = re.sub(r'[^A-Z0-9]', '-', name.upper())
    clean = re.sub(r'-+', '-', clean).strip('-')
    return clean[:20]

