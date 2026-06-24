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
    Convert each PDF page to JPEG base64 via pymupdf.
    Resolution: 96 DPI (Matrix 1.33x) — readable by Haiku Vision, well under Anthropic 5 MB/image limit.
    Images exceeding 4 MB after encoding are skipped with a warning rather than crashing.

    Returns:
        List of base64 strings (one per page).
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images_b64 = []

    # Anthropic hard limit: 5 MB per image. We target < 4 MB to stay safe.
    MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB

    num_pages = min(len(doc), MAX_VISION_PAGES)
    for page_num in range(num_pages):
        page = doc[page_num]
        # 96 DPI = matrix 1.33x — good balance between readability and file size
        # PNG at 2x (old value) produced 5-15 MB files for large-format flyers.
        mat = fitz.Matrix(1.33, 1.33)
        pix = page.get_pixmap(matrix=mat)

        # Hard cap: if either dimension exceeds 1800px, downscale to fit.
        # Anthropic Vision reads text fine at 1200-1800px. Above that = wasted tokens + risk of 400.
        MAX_DIM = 1800
        if pix.width > MAX_DIM or pix.height > MAX_DIM:
            scale = MAX_DIM / max(pix.width, pix.height)
            mat2 = fitz.Matrix(1.33 * scale, 1.33 * scale)
            pix = page.get_pixmap(matrix=mat2)

        # JPEG is 5-10x smaller than PNG for typical catalog/flyer content
        jpeg_bytes = pix.tobytes("jpeg", jpg_quality=85)

        if len(jpeg_bytes) > MAX_IMAGE_BYTES:
            # Page too large even at reduced res — skip it rather than crash Anthropic
            print(f"[PDF EXTRACTOR] Page {page_num + 1} skipped: {len(jpeg_bytes) / 1024 / 1024:.1f} MB > 4 MB limit")
            continue

        print(f"[PDF EXTRACTOR] Page {page_num + 1}: {pix.width}x{pix.height}px, {len(jpeg_bytes) / 1024:.0f} KB")
        images_b64.append(base64.standard_b64encode(jpeg_bytes).decode("utf-8"))

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
                "media_type": "image/jpeg",
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

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=8192,  # raised from 4096 — large catalogs need more output tokens
            messages=[{"role": "user", "content": content}]
        )
    except anthropic.BadRequestError as e:
        # Anthropic rejected the request (image too large, too many tokens, etc.)
        raise ValueError(
            f"Anthropic rejected the request: {str(e)}. "
            "Try a smaller PDF or reduce the number of pages."
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

    # Truncate at 60 000 chars (~100 pages of dense catalog text).
    # 15 000 was too aggressive — a 36-page catalog easily exceeds it.
    if len(raw_text) > 60_000:
        raw_text = raw_text[:60_000] + "\n[... content truncated ...]"
    
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
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    return _parse_haiku_response(message.content[0].text)

# ----------------------------------------------------
# PARSING + VALIDATION PYDANTIC
# ----------------------------------------------------

def _parse_haiku_response(response_text: str) -> List[ExtractedProduct]:
    """
    Parse Haiku's response into a list of ExtractedProduct.

    Handles 4 cases in order:
      1. Clean JSON array (ideal)
      2. JSON array inside ```json ... ``` code block
      3. JSON array found anywhere in surrounding prose
      4. TRUNCATED response — salvage all complete {objects} character by character
         (happens when the catalog is large and Haiku hits max_tokens mid-array)
    """
    response_text = response_text.strip()

    # Strip ```json ... ``` or ``` ... ``` code block markers (Haiku adds these despite instructions)
    response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
    response_text = re.sub(r'\s*```\s*$', '', response_text)
    response_text = response_text.strip()

    raw_list = None

    # Attempt 1: direct JSON parse
    try:
        raw_list = json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find a complete JSON array anywhere in the text
    if raw_list is None:
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            try:
                raw_list = json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

    # Attempt 3: Haiku wrapped in {"products": [...]}
    if raw_list is None:
        obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if obj_match:
            try:
                obj = json.loads(obj_match.group(0))
                raw_list = next((v for v in obj.values() if isinstance(v, list)), None)
            except json.JSONDecodeError:
                pass

    # Attempt 4: TRUNCATED response — walk character by character, salvage complete objects.
    # This fires when max_tokens cuts Haiku mid-JSON (e.g. "formats": <cut>).
    if raw_list is None:
        salvaged = []
        depth = 0
        obj_start = None
        for i, ch in enumerate(response_text):
            if ch == '{':
                if depth == 0:
                    obj_start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and obj_start is not None:
                    fragment = response_text[obj_start:i + 1]
                    try:
                        obj = json.loads(fragment)
                        if isinstance(obj, dict):
                            salvaged.append(obj)
                    except json.JSONDecodeError:
                        pass
                    obj_start = None
        if salvaged:
            print(f"[PDF EXTRACTOR] Truncated response — salvaged {len(salvaged)} complete objects")
            raw_list = salvaged

    if raw_list is None:
        raise ValueError(
            f"Haiku did not return parseable JSON.\n"
            f"Response preview: {response_text[:400]}"
        )

    if not isinstance(raw_list, list):
        raise ValueError("Haiku response is not a JSON array.")

    products = []
    seen = set()
    for item in raw_list:
        try:
            product = ExtractedProduct(**item)
            key = product.item_number.upper().strip()
            if key not in seen:
                seen.add(key)
                products.append(product)
        except Exception:
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
        # PDF native with text -> text mode (fewer tokens, faster)
        products = _extract_products_from_text(raw_text)
        if not products:
            # Text extraction returned nothing — fallback to Vision
            images_b64 = _pdf_pages_to_images(file_bytes)
            if images_b64:  # fixed: was "if not images_b64" (inverted condition)
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

def generate_catalog_pitch_with_ai(
    catalog_name: str,
    products: List[ExtractedProduct],
) -> str:
    """
    Génère un pitch court (2 phrases max) à partir des produits extraits.
    Non bloquant: retourne "" si l'IA échoue.
    """
    if not products:
        return ""
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    sample = products[:25]
    product_lines = []
    for p in sample:
        bits = [p.name]
        if p.category:
            bits.append(f"cat={p.category}")
        if p.brand:
            bits.append(f"brand={p.brand}")
        if p.formats:
            bits.append(f"formats={p.formats}")
        product_lines.append(" | ".join(bits))

    prompt = f"""
You are a B2B food distribution copywriter.
Write ONE short "catalog pitch" paragraph for a sales email campaign.

Goal: Present the BRAND globally + the product RANGE  at high level - without listing individual items.

Constraints:
- Max 2 sentences
- 220 - 230 characters ideally
- Concerete, product-focused, not generic, commercial tone
- No markdown, no bullets, no quotes
- Focus on brand heritage/reputation + range breadth (not individual SKUs)
- Language: use English

Catalog name: {catalog_name}

Products sample (use only to infer brand positioning and category breadth):
{chr(10).join(product_lines)}
""".strip()
    
    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}]
        )
        text = (message.content[0].text or "").strip()
        text = re.sub(r"\s+", " ", text).strip(" \"'")
        return text[:360]
    except Exception:
        return ""
    
async def improve_text_with_ai(text: str) -> str:
    """
    Improve catalog text with Claude Haiku and always return English output.
    """
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a professional B2B copy editor for food distribution catalog descriptions.

Rewrite and improve the text with:
- Correct grammar and spelling
- Better clarity and concision
- Professional commercial tone
- Natural sentence flow

Critical rule: ALWAYS return the final result in English, even if the original text is in French or another language.
Keep product names and brand names unchanged when possible.
Return ONLY the improved English text. No explanations, no bullets, no quotes.

Original text:
{text}"""
                }
            ]
        )

        improved = message.content[0].text.strip()
        return improved
    
    except Exception:
        return text