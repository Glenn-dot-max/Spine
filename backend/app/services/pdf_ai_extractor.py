"""
SPINE V1 - pdf_ai_extractor
===========================
Rôle : Extraction intelligente de produits depuis un catalogue PDF via Claude Haiku Vision.
       Stratégie hybride :
        1. pdfplumber tente l'extraction texte (PDFs scannés / image)
        2. Si texte insuffisant (< 100 chars) -> fallback Vision (PDFs scannés / image)
Dépendances : pdfplumber, pymupdf (fitz), anthropic, app.core.config
Utilisé par : routes/product_import.py
Sécurité : Le PDF contient uniquement des données produits (pas de PII).
           Les images de pages sont envoyées à Anthropic - ne jamais utiliser pour des docs clients.
À faire : Chunking pour PDFs > 20 pages en vision mode (coût tokens).
Dernière modification : 2026 - 06 - 05 - Refont vision pour catalogues image.
"""

import pdfplumber
import fitz  # PyMuPDF
import anthropic
import json
import io
import re
import base64
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.config import ANTHROPIC_API_KEY

# Seuil : si pdfplumber extrait moins de 500 chars par page -> PDF image -> Vision
TEXT_LENGTH_THRESHOLD = 500
# Max pages envoyées en vision (coût tokens : ~ 1500 tokens/page)
MAX_VISION_PAGES = 15

class ExtractedProduct(BaseModel):
    """
    Produit extrait d'un PDF par Haiku.
    confidence : score auto-évalué par haiku sur la qualité de l'extraction (0-1).
    """
    item_number: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    brand: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    formats: Optional[str] = None
    price_range: Optional[str] = None
    certifications: Optional[str] = None
    segments: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    @field_validator("item_number", "name", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return str(v).strip() if v else v
    
# ----------------------------------------------------
# EXTRACTION TEXTE (PDFs natifs)
# ----------------------------------------------------

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Tente d'extraire le texte brut avec pdfplumber.
    Retourne la chaîne vide si le PDF est image-only.
    """
    pages_text = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f" [PAGE {i + 1}]\n{text.strip()}")
    except Exception as e:
        return ""
    return "\n\n".join(pages_text)

def _is_text_sufficent(text: str, num_pages: int) -> bool:
    """
    Détermine si le texte extrait est suffisant pour éviter le fallback Vision.
    Critère : au moins TEXT_FALLBACK_THRESHOLD chars par page en moyenne.
    """
    if not text or num_pages == 0:
        return False
    avg_chars_per_page = len(text) / num_pages
    return avg_chars_per_page >= TEXT_LENGTH_THRESHOLD


# ----------------------------------------------------
# EXTRACTION VISION (PDFs scannés / image)
# ----------------------------------------------------

def _pdf_pages_to_images(file_bytes: bytes) -> List[str]:
    """
    Convertit chaque page du PDF en PNG base64 via pymupdf.
    Résolution 150 DPI — suffisant pour la lecture Haiku, léger en tokens.

    Returns:
        Liste de strings base64 (une par page).
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images_b64 = []

    num_pages = min(len(doc), MAX_VISION_PAGES)
    for page_num in range(num_pages):
        page = doc[page_num]
        # 150 DPI = matrix 1.5x (72 DPI natif x 1.5 = 108 DPI, x2 = 144)
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        images_b64.append(base64.standard_b64encode(png_bytes).decode("utf-8"))
    
    doc.close()
    return images_b64

def _extract_products_from_images(images_b64: List[str]) -> List[ExtractedProduct]:
    """
    Envoie les pages (images PNG base64) à Claude Haiku Vision.
    Toutes les pages sont envoyées dans un seul message pour que Haiku
    puisse consolider les informations produits qui s'étendent sur plusieurs pages.

    Returns:
        Lest de ExtractedProduct validés.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Construction du contenu : une image par page, instructuion finale
    content = []
    for i, img_b64 in enumerate(images_b64):
        content.append({
            "type": "text",
            "text": f"Page {i + 1} of the product catalog:"
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64
            }
        })

    content.append({
        "type": "text",
        "text": """Extract ALL products visible in these catalog pages and return a JSON array.
        
For each product extract:
- item_number: SKU, reference code, or product code (REQUIRED). If none found, generate a short slug from the name (e.g. "PROD-DIJON-MUSTARD")
- name: full product name (REQUIRED)
- brand: brand or manufacturer name
- short_description: brief product description
- category: product category (e.g. mustard, vinegar, cheese, charcuterie, olive oil, condiment)
- formats: available sizes/formats comma-separated (e.g. "1L bottle, case of 12, 5L bag-in-box")
- price_range: price if visible (e.g. "$4.50/unit", "$2.20-$2.60/kg")
- certifications: quality certifications comma-separated (e.g. "Organic, Kosher, Non-GMO")
- segments: target market comma-separated (e.g. "foodservice, retail, industry")
- confidence: your confidence score from 0.0 to 1.0 for this extraction

Return ONLY a valid JSON array. No explanation, no markdown, no code blocks.
Example: [{"item_number": "CLOV-001", "name": "Dijon Mustard", "brand": "Clovis", "category": "mustard", "confidence": 0.9}]
"""
    })

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}]
    )

    return _parse_haiku_response(message.content[0].text)

# ----------------------------------------------------
# EXTRACTION TEXTE VIA IA (PDFs natifs)
# ----------------------------------------------------

def _extract_products_from_text(raw_text: str) -> List[ExtractedProduct]:
    """
    Envoie le texte brut extrait par pdfplumber à Haiku pour structuration.
    Utilisé uniquement si le PDF contient du texte suffisant.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Troncature à 15 000 chars pour rester dans les limites de tokens
    if len(raw_text) > 15_000:
        raw_text = raw_text[:15_000] + "\n[... contenu tronqué ...]"
    
    prompt = f"""Extract all products from this product catalog text and return them as JSON array.

For each product :
-item_number: SKU or product code (REQURED, generate slug if missing)
-name: full product name (REQUIRED)
- brand, short, description, category, formats, price_range, certifications, segments: if available
- confidence: your confidence score 0.0 to 1.0

Return ONLY a valid JSON array. No markdown, no explanation?

CATALOG TEXT:
{raw_text}"""
    
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return _parse_haiku_response(message.content[0].text)

# ----------------------------------------------------
# PARSING + VALIDATION PYDANTIC
# ----------------------------------------------------

def _parse_haiku_response(response_text: str) -> List[ExtractedProduct]:
    """
    Nettoie la réponse Haiku, parse le JSON, valide avec Pydantic, dédoublonne.

    Returns:
        Liste de ExtractedProduct validés et dédoublonnés par item_number.
    """
    # Nettoyage backticks éventuels
    response_text = response_text.strip()
    response_text = re.sub(r"^```json\s*", "", response_text)
    response_text = re.sub(r"^```\s*", "", response_text)
    response_text = re.sub(r"\s*```$", "", response_text)

    try:
        raw_list = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Haiku n'a pas retourné de JSON valide : {str(e)}\n"
            f"Début de réponse : {response_text[:300]}"
        )
    
    if not isinstance(raw_list, list):
        raise ValueError("La réponse Haiku n'est pas un tableau JSON.")
    
    products = []
    seen = set()
    for item in raw_list:
        try:
            product = ExtractedProduct(**item)
            key = product.item_number.upper().strip()
            if key not in seen:
                seen.add(key)
                products.append(product)
        except Exception as e:
            continue
        
    return products

# ----------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# ----------------------------------------------------

def extract_products_with_ai(file_bytes: bytes) -> List[ExtractedProduct]:
    """
    Pipeline principal d'extraction produits depuis un PDF.

    Stratégie hybride automatique :
      - Si le PDF contient du texte suffisant -> extraction texte + Haiku text
      - Si le PDF est image-only ou pauvre en texte -> conversion PNG + Haiku Vision
    
    Args:
        file_bytes: contenu brut du fichier PDF.

    Returns:
        Liste de ExtractedProduct validés, dédoublonnés, prêts pour import DB.

    Raises:
        ValueError: Si le PDF est illisible ou si Haiku retourne une réponse invalide.
    """
    # Détermine le nombre de pages
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        num_pages = len(doc)
        doc.close()
    except Exception as e:
        num_pages = 1
    
    # Tentative texte
    raw_text = _extract_text_from_pdf(file_bytes)

    if _is_text_sufficent(raw_text, num_pages):
        # PDF natif avec texte -> mode texte (moins de tokens, plus rapide)
        products = _extract_products_from_text(raw_text)
        if not products:
            images_b64 = _pdf_pages_to_images(file_bytes)
            if not images_b64:
                return _extract_products_from_images(images_b64)
        return products
        
    else:
        # PDF image -> mode Vision
        images_b64 = _pdf_pages_to_images(file_bytes)
        if not images_b64:
            raise ValueError(
                "Impossible de converir le PDF en images. "
                "Vérifiez que le fichier n'est pas corrompu."
            )
        return _extract_products_from_images(images_b64)

