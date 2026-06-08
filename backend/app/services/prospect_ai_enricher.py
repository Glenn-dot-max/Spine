"""
SPINE V1 — prospect_ai_enricher
================================
Role: AI enrichment of imported leads via Claude Haiku.
      Pipeline:
        1. Column mapping: file headers -> Spine fields (1 call per file)
        2. Batch enrichment: product catalog matching + CRM note rewrite
                             + type_structure / segment / canal inference
Dependencies: anthropic, pydantic, app.core.config
Used by: routes/prospect_import.py
Security: NEVER send PII (email, first_name, last_name) to Anthropic.
          Only: company_name, position, source_notes, collateral_raw.
Todo: Auto-chunking if > 50 rows per batch.
Last modified: 2026-06-06 — initial creation
"""

import anthropic
import json
import re
from typing import Optional
from pydantic import BaseModel

from app.core.config import ANTHROPIC_API_KEY

SPINE_FIELDS = [
    "email", "first_name", "last_name", "company_name",
    "position", "phone_number", "source_notes", "canal", "product_interest",
]

STRUCTURE_TYPES = [
    "restaurant", "distributor", "hotel", "specialty_food_store",
    "caterer", "supermarket", "wholesaler", "importer", "broker", "other",
]

SEGMENTS = [
    "fine_dining", "casual_dining", "retail", "foodservice",
    "hospitality", "institutional", "other",
]

CANALS = [
    "trade_show", "linkedin", "referral", "emailing", "inbound", "other",
]

# ------------------------------------------------------------
# DATA MODELS
# ------------------------------------------------------------

class ProductMatch(BaseModel):
    """A catalog product matching the lead's declared interest."""
    product_id: int
    product_name: str
    item_number: str
    confidence: float # 0.0 to 1.0

class LeadCategory(BaseModel):
    """Ai-inferred categorization of the lead."""
    type_structure: Optional[str] = None  # e.g. restaurant, distributor...
    segment: Optional[str] = None         # e.g. fine dining, retail...
    inferred_canal: Optional[str] = None  # e.g. trade_show, linkedin...
    confidence: float = 0.0               # overall confidence in the categorization


class EnrichedRow(BaseModel):
    """Result of AI enrichment for one import row."""
    row_index: int
    # Fields mapped from the file
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    position: Optional[str] = None
    phone_number: Optional[str] = None
    collateral_raw: Optional[str] = None
    canal_raw: Optional[str] = None
    # AI-enriched fields  
    clean_note: Optional[str] = None                # rewritten CRM note
    product_matches: list[ProductMatch] = []        # confidence >= 0.75
    product_suggestions: list[ProductMatch] = []    # confidence < 0.75
    category: Optional[LeadCategory] = None
    # Raw data for review UI
    original_row: dict = {}

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _haiku_client() -> anthropic.Anthropic:
    """Initialize and return an Anthropic client."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def _clean_json(raw: str) -> str:
    """Extract JSON from a Haiku response that may contain surrounding text."""
    match = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
    return match.group(0) if match else raw

# ------------------------------------------------------------
# 1. COLUMN MAPPING
# ------------------------------------------------------------

def analyze_column_mapping(
        headers: list[str],
        sample_rows: list[dict],
) -> dict[str, Optional[str]]:
    """
    Send file headers + 3 samples rows to Haiku.
    Returns {orginal_header: spine_fiels | null}.

    Examples of columbs recognized automatically:
    - "Attendee Company", "Organisation", "Société" -> company_name
    - "Interest Area", "Collateral", "Produits souhaités" → product_interest
    - "Badge Notes", "Rep Comments", "Remarques" → source_notes
    - "Lead Origin", "Source", "Provenance" → canal
    """
    client = _haiku_client()

    sample_str = json.dumps(sample_rows[:3], ensure_ascii=False, indent=2)
    fields_str = ", ".join(SPINE_FIELDS)

    prompt = f"""You are a data mapping assistant for a food distribution CRM.

Headers of the imported file:
{json.dumps(headers)}

Sample data (first 3 rows):
{sample_str}

Available Spine CRM fields: {fields_str}

Task: Map each header to the most appropriate Spine field.
- Return ONLY a JSON object: {{"original_header": "spine_field_or_null"}}
- Use null if the column has no relevant CRM field.
- "product_interest" = any column about products the contact is interested in (collateral, interest area, produits...).
- "source_notes" = any column with sales notes, comments, remarks, badge notes, rep notes.
- "canal" = lead origin / acquisition source / how they were met.
- Headers may be in French, English, Spanish or any language — map them correctly regardless.
- Do not add any explanation, only the JSON object."""
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        mapping = json.loads(_clean_json(raw))
        return {
            k: (v if v in SPINE_FIELDS else None)
            for k, v in mapping.items()
        }
    except Exception:
        return {h: None for h in headers}
    
# ------------------------------------------------------------
# 2. BATCH ENRICHMENT
# ------------------------------------------------------------

def enrich_rows_batch(
        rows: list[dict],
        catalog_products: list[dict],
) -> list[dict]:
    """
    Send all rows to Haiku in a single call.
    For each row returns:
      - clean_note: professional CRM note rewritten in English
      - product_matches: catalog products matching product_interest
      - type_structure, segment, inferred_canal, category_confidence
    
    SECURITY: email, first_name, last_name are NEVER sent to Haiku.
    Only company_name, position, source_notes, product_interest are sent.
    """
    if not rows:
        return []
    
    client = _haiku_client()

    # Anonymized data only - no PII
    safe_rows = [
        {
            "idx": r.get("_row_index", i),
            "company": r.get("company_name", ""),
            "position": r.get("position", ""),
            "notes": r.get("source_notes", ""),
            "product_interest": r.get("product_interest", ""),
            "canal_raw": r.get("canal_raw", "") or r.get("canal", ""),
        }
        for i, r in enumerate(rows)
    ]

    # Catalog summary - max 100 products to control token cost
    cataloh_summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "item_number": p.get("item_number", ""),
        }
        for p in catalog_products[:100]
    ]

    types_str = ", ".join(STRUCTURE_TYPES)
    segments_str = ", ".join(SEGMENTS)
    canals_str = ", ".join(CANALS)

    prompt = f"""You are a CRM enrichmet assistant for a food distribution company.

CATALOG (available products):
{json.dumps(cataloh_summary, ensure_ascii=False)}

LEADS TO ENRICH:
{json.dumps(safe_rows, ensure_ascii=False)}

For each lead (identified by "idx"), return:
1. clean_note: Rewrite "notes" as a concise professional CRM note in English. Max 2 sentences. Empty string if no notes.
2. product_matches: Products from CATALOG matching "product_interest". Each: {{"product_id": int, "confidence": float 0-1}}. Empty list if no match.
3. type_structure: Best guess from [{types_str}] based on company/position. null if unknown.
4. segment: Best guess from [{segments_str}]. null if unknown.
5. inferred_canal: Best guess from [{canals_str}] based on canal_raw. null if unknown.
6. category_confidence: float 0-1 overall confidence on type/segment inference.

Return ONLY a JSON array:
[
  {{
    "idx": 0,
    "clean_note": "...",
    "product_matches": [{{"product_id": 1, "confidence": 0.9}}],
    "type_structure": "restaurant",
    "segment": "fine_dining",
    "inferred_canal": "trade_show",
    "category_confidence": 0.85
  }},
]
No explanation, oly the JSON array."""
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        return json.loads(_clean_json(raw))
    except Exception:
        return [{"idx": r.get("_row_index", i)} for i, r in enumerate(rows)]

# ------------------------------------------------------------
# 3. FINAL ASSEMBLY
# ------------------------------------------------------------

def build_enriched_rows(
        mapped_rows: list[dict],
        enrichment_results: list[dict],
        catalog_products: list[dict],
) -> list[EnrichedRow]:
    """
    Combine mapped data + Haiku enrichments into EnrichedRow objects
    ready for the frontend review UI.
    - product_matches: confidence >= 0.75 -> auto-link proposed
    - product_suggestions: confidence < 0.75 -> user decides
    """
    products_by_id = {p["id"]: p for p in catalog_products}
    enrichment_by_idx = {r.get("idx", i): r for i, r in enumerate(enrichment_results)}

    result = []
    for i, row in enumerate(mapped_rows):
        idx = row.get("_row_index", i)
        enrich = enrichment_by_idx.get(idx, {})

        matches = []
        suggestions = []
        for pm in enrich.get("product_matches", []):
            pid = pm.get("product_id")
            conf = float(pm.get("confidence", 0))
            product = products_by_id.get(pid)
            if not product:
                continue
            match_obj = ProductMatch(
                product_id=pid,
                product_name=product["name"],
                item_number=product["item_number"],
                confidence=conf,
            )
            if conf >= 0.75:
                matches.append(match_obj)
            else:
                suggestions.append(match_obj)

        category = None
        if enrich.get("type_structure") or enrich.get("segment"):
            category = LeadCategory(
                type_structure=enrich.get("type_structure"),
                segment=enrich.get("segment"),
                inferred_canal=enrich.get("inferred_canal"),
                confidence=float(enrich.get("category_confidence", 0.5)),
            )

        result.append(
            EnrichedRow(
                row_index=idx,
                email=row.get("email"),
                first_name=row.get("first_name"),
                last_name=row.get("last_name"),
                company_name=row.get("company_name"),
                position=row.get("position"),
                phone_number=row.get("phone_number"),
                collateral_raw=row.get("product_interest"),
                canal_raw=row.get("canal_raw") or row.get("canal"),
                clean_note=enrich.get("clean_note") or row.get("source_notes"),
                product_matches=matches,
                product_suggestions=suggestions,
                category=category,
                original_row={k: v for k, v in row.items() if not k.startswith("_")},
            )
        )

    return result
