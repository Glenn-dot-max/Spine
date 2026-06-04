"""
SPINE V1 — prospect_import
==========================
Rôle : Import/export bulk de prospects (XLSX, XLS, CSV, TSV, TXT)
       avec mapping de colonnes générique multi-salon.
Dépendances : pandas, app.models.prospect, app.models.prospect_product, app.models.product
Utilisé par : frontend (écran prospects/import)
Sécurité : user_id filtré sur toutes les requêtes; pas de logs de contenu sensible.
À faire : matching produit plus avancé (brand + item_number + synonymes) + mode preview des collisions.
Dernière modification : 2026-06-03 — mapping générique multi-salon + corrections bugs import.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import io
import re

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.prospect import Prospect, ProspectSource, ProspectCanal
from app.models.prospect_product import ProspectProduct
from app.models.product import Product
from app.models.campaign import CampaignContact

router = APIRouter(prefix="/api/prospects", tags=["prospect-import"])


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def clean_value(value) -> Optional[str]:
    """
    Normalise une valeur de cellule :
    - None, NaN, chaîne vide, '.', 'nan', 'none', 'n/a' -> None
    - Sinon : strip des espaces
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in ("", "nan", "none", "n/a", "na", ".", "-"):
        return None
    return s


def normalize_header_name(header: str) -> str:
    """
    Normalise un nom de colonne pour matching robuste :
    - lowercase
    - retire espaces / underscores / tirets / ponctuation
    """
    raw = str(header).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", raw)


def read_uploaded_dataframe(filename: str, contents: bytes) -> pd.DataFrame:
    """
    Lit un fichier uploadé (xlsx, xls, csv, tsv, txt) et retourne un DataFrame.
    Lève ValueError si format non supporté.
    """
    name = filename.lower()

    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(contents))

    if name.endswith((".csv", ".tsv", ".txt")):
        # sep=None + engine=python => auto-detect séparateur (, ; tab)
        return pd.read_csv(io.BytesIO(contents), sep=None, engine="python")

    raise ValueError("Format non supporté. Utilise XLSX, XLS, CSV, TSV ou TXT.")


# Mapping canonique multi-salon (pas spécifique NRA)
# clé = header normalisé (normalize_header_name), valeur = champ cible interne
_GENERIC_COLUMN_MAP = {
    # email
    "email": "email",
    "emailaddress": "email",
    "mail": "email",
    "courriel": "email",
    "adresseemail": "email",
    "vendoremail": "vendor_email",  # Garder séparé du prospect email

    # prénom
    "first": "first_name",
    "firstname": "first_name",
    "givenname": "first_name",
    "prenom": "first_name",
    "forename": "first_name",

    # nom
    "last": "last_name",
    "lastname": "last_name",
    "surname": "last_name",
    "familyname": "last_name",
    "nom": "last_name",

    # entreprise
    "company": "company_name",
    "companyname": "company_name",
    "organization": "company_name",
    "organisation": "company_name",
    "account": "company_name",
    "societe": "company_name",
    "entreprise": "company_name",

    # poste
    "title": "position",
    "jobtitle": "position",
    "position": "position",
    "role": "position",
    "fonction": "position",
    "poste": "position",

    # téléphone
    "phone": "phone_number",
    "phonenumber": "phone_number",
    "mobile": "phone_number",
    "telephone": "phone_number",
    "tel": "phone_number",

    # notes
    "notes": "source_notes",
    "comments": "source_notes",
    "commentaires": "source_notes",
    "remarques": "source_notes",

    # canal brut
    "leadorigin": "canal_raw",
    "origin": "canal_raw",
    # "source": "canal_raw",  # retiré : trop ambigu selon les exports salons
    "acquisitionsource": "canal_raw",

    # intérêt produit
    "collateral": "collateral",
    "collaterals": "collateral",
    "productinterest": "collateral",
    "productsinterest": "collateral",
    "interetproduit": "collateral",
    "produitsinteret": "collateral",

    # enrichissement notes
    "purchasetimeframe": "purchase_timeframe",
    "purchasetime": "purchase_timeframe",
    "timeframe": "purchase_timeframe",
    "purchaseauthorization": "purchase_auth",
    "authorization": "purchase_auth",
    "regtypecode": "reg_type_code",
    "badge": "reg_type_code",
    "salesrep": "sales_rep",
    "ownerrep": "sales_rep",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomme les colonnes vers un schéma interne stable :
    email, first_name, last_name, company_name, position, phone_number,
    source_notes, canal_raw, canal, canal_detail, collateral, ...
    """
    rename_map = {}

    for col in df.columns:
        normalized = normalize_header_name(col)
        target = _GENERIC_COLUMN_MAP.get(normalized)

        # Heuristiques de secours si pas de match exact
        if target is None:
            if normalized == "first" or ("first" in normalized and "name" in normalized):
                target = "first_name"
            elif normalized == "last" or ("last" in normalized and "name" in normalized) or "surname" in normalized:
                target = "last_name"
            elif normalized == "email" or ("mail" in normalized and "vendor" not in normalized):
                target = "email"
            elif "company" in normalized or "societe" in normalized or "entreprise" in normalized:
                target = "company_name"
            elif "phone" in normalized or "mobile" in normalized or "tel" in normalized:
                target = "phone_number"
            elif ("job" in normalized and "title" in normalized) or "position" in normalized or "role" in normalized:
                target = "position"
            elif "origin" in normalized or "source" in normalized:
                target = "canal_raw"
            elif "note" in normalized or "comment" in normalized:
                target = "source_notes"
            elif "collateral" in normalized or ("product" in normalized and "interest" in normalized):
                target = "collateral"

        if target:
            rename_map[col] = target

    if rename_map:
        df = df.rename(columns=rename_map)

    return df

def coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fusionne les colonnes dupliquées après normalisation
    en gardant la 1re valeur non par ligne.
    """
    if not df.columns.duplicated().any():
        return df
    
    merged = pd.DataFrame(index=df.index)
    ordered_unique = list(dict.fromkeys(df.columns.tolist()))  

    for col in ordered_unique:
        subset = df.loc[:, df.columns == col]
        if isinstance(subset, pd.Series):
            merged[col] = subset
        else:
            merged[col] = subset.bfill(axis=1).iloc[:, 0]

    return merged

def looks_like_person_name(value: str) -> bool:
    """Heuristique simple pour détecter si une valeur ressemble à un nom."""
    s = value.strip()
    if not s:
        return False
    parts = [p for p in re.split(r"[\s,]+", s) if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    return all(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ'-]+$", p) for p in parts)

# Mapping Lead Origin -> ProspectCanal
_CANAL_MAP = {
    "trade show": ProspectCanal.trade_show,
    "tradeshow": ProspectCanal.trade_show,
    "exhibition": ProspectCanal.trade_show,
    "event": ProspectCanal.trade_show,
    "salon": ProspectCanal.trade_show,
    "foire": ProspectCanal.trade_show,

    "linkedin": ProspectCanal.linkedin,

    "referral": ProspectCanal.referral,
    "referred": ProspectCanal.referral,
    "reference": ProspectCanal.referral,
    "word of mouth": ProspectCanal.referral,
    "boucheoreille": ProspectCanal.referral,

    "emailing": ProspectCanal.emailing,
    "email": ProspectCanal.emailing,
    "newsletter": ProspectCanal.emailing,
    "cold email": ProspectCanal.emailing,

    "inbound": ProspectCanal.inbound,
    "website": ProspectCanal.inbound,
    "web": ProspectCanal.inbound,
    "contact form": ProspectCanal.inbound,
}


def detect_canal(raw: Optional[str]) -> tuple[Optional[ProspectCanal], Optional[str]]:
    """
    Analyse la valeur brute et retourne (canal_enum, canal_detail).
    Ignore les valeurs qui ressemblent à des noms de personnes.
    """
    if not raw:
        return None, None

    detail = raw.strip()
    lower = detail.lower()

    for key, value in _CANAL_MAP.items():
        if key in lower:
            return value, detail

    if looks_like_person_name(detail):
        return None, None
    
    return ProspectCanal.other, detail


def build_enriched_notes(row: pd.Series, base_notes: Optional[str]) -> Optional[str]:
    """
    Construit une note enrichie en combinant des champs annexes.
    """
    parts = []
    if base_notes:
        parts.append(base_notes)

    for field, label in [
        ("purchase_timeframe", "Purchase timeframe"),
        ("purchase_auth", "Purchase auth"),
        ("reg_type_code", "Badge type"),
        ("sales_rep", "Sales rep"),
    ]:
        val = clean_value(row.get(field))
        if val:
            parts.append(f"{label}: {val}")

    return " | ".join(parts) if parts else None


def find_product_by_collateral(
    collateral_raw: Optional[str],
    user_id: int,
    db: Session
) -> list[int]:
    """
    Tente de matcher la valeur Collateral avec les produits user.
    Retourne une liste de product_id.
    """
    if not collateral_raw:
        return []

    product_ids = []
    tokens = re.split(r"[,;/]+", collateral_raw)

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        match = db.query(Product).filter(
            Product.user_id == user_id,
            Product.name.ilike(f"%{token}%")
        ).first()

        if match and match.id not in product_ids:
            product_ids.append(match.id)

    return product_ids


def infer_source_from_canal(canal: Optional[ProspectCanal]) -> ProspectSource:
    """Map canal -> source CRM."""
    if canal == ProspectCanal.trade_show:
        return ProspectSource.trade_show
    if canal == ProspectCanal.referral:
        return ProspectSource.referral
    if canal == ProspectCanal.inbound:
        return ProspectSource.inbound
    return ProspectSource.other


# -------------------------------------------------
# ENDPOINTS
# -------------------------------------------------

@router.get("/import/template")
def download_prospect_template():
    """Télécharge un template standard d'import prospects."""
    example_data = {
        "email": ["john.doe@example.com", "marie.martin@bistro.fr"],
        "first_name": ["John", "Marie"],
        "last_name": ["Doe", "Martin"],
        "company_name": ["Bistro Example", "Restaurant Paris"],
        "position": ["Chef", "Owner"],
        "phone_number": ["+1 555 123 4567", "+33 1 23 45 67 89"],
        "source_notes": ["Met at spring show", "LinkedIn outreach"],
        "canal": ["trade_show", "linkedin"],
        "canal_detail": ["Food Expo Chicago", ""],
        "collateral": ["mustard; balsamic vinegar", "vinaigre"],
    }

    df = pd.DataFrame(example_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Prospects")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=prospect_import_template.xlsx"},
    )


@router.post("/import/preview")
async def preview_prospect_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prévisualise un fichier avant import :
    - support multi-format
    - mapping de colonnes
    - avertissements qualité
    """
    try:
        contents = await file.read()
        df = read_uploaded_dataframe(file.filename, contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lecture fichier: {str(e)}")

    df = normalize_columns(df)
    df = coalesce_duplicate_columns(df)
    warnings = []

    required = ["email", "first_name", "last_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Colonnes manquantes après normalisation: {', '.join(missing)}. "
                f"Colonnes détectées: {', '.join(df.columns.tolist())}"
            ),
        )

    emails = df["email"].apply(clean_value)
    empty_emails = emails.isna().sum()
    if empty_emails:
        warnings.append(f"⚠️ {empty_emails} ligne(s) sans email (ignorées à l'import).")

    invalid_emails = emails.dropna().apply(lambda e: "@" not in e).sum()
    if invalid_emails:
        warnings.append(f"⚠️ {invalid_emails} email(s) au format invalide (ignorés à l'import).")

    dups = emails.dropna().duplicated(keep=False).sum()
    if dups:
        warnings.append(f"⚠️ {dups} email(s) en doublon dans le fichier.")

    empty_names = df.apply(
        lambda r: not clean_value(r.get("first_name")) or not clean_value(r.get("last_name")),
        axis=1
    ).sum()
    if empty_names:
        warnings.append(f"⚠️ {empty_names} ligne(s) avec prénom/nom manquant(s).")

    if "canal_raw" in df.columns:
        warnings.append("✅ Canal détectable via colonne source/origin.")
    if "collateral" in df.columns:
        warnings.append("✅ Colonne intérêt produit détectée (liaison produit tentée à l'import).")

    if not warnings:
        warnings.append("✅ Fichier valide. Aucun problème détecté.")

    sample_raw = df.head(5).fillna("").to_dict(orient="records")

    # Marquer les emails déjà connus dans le DB pour cet user
    sample = []
    for row in sample_raw:
        email_val = str(row.get("email", "")).strip().lower()
        already_exists = False
        if email_val and "@" in email_val:
            exists = db.query(Prospect).filter(
                Prospect.user_id == current_user.id,
                Prospect.email == email_val
            ).first() is not None
        sample.append({**row, "_already_exists": already_exists})
    
    all_emails = df["email"].apply(clean_value).dropna().str.lower().tolist()
    existing_count = sum(
        1 for e in all_emails
        if db.query(Prospect).filter(
            Prospect.user_id == current_user.id,
            Prospect.email == e,
        ).first() is not None
    )
    if existing_count > 0:
        warnings.append(
            f"ℹ️ {existing_count} email already exists in your database "
            "(shown in preview with _already_exists=true)."
        )
            

    return {
        "total_rows": len(df),
        "columns_detected": df.columns.tolist(),
        "sample_data": sample,
        "warnings": warnings,
    }


@router.post("/import")
async def import_prospects(
    file: UploadFile = File(...),
    update_existing: bool = False,
    campaign_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Importe des prospects :
    - multi-format
    - mapping colonnes générique
    - enrichissement canal/canal_detail
    - lien ProspectProduct depuis colonne collateral
    """
    try:
        contents = await file.read()
        df = read_uploaded_dataframe(file.filename, contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lecture fichier: {str(e)}")

    df = normalize_columns(df)
    df = coalesce_duplicate_columns(df)

    required = ["email", "first_name", "last_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Colonnes manquantes: {', '.join(missing)}")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    imported_prospect_ids: list[int] = []

    for index, row in df.iterrows():
        try:
            # Obligatoires
            email = clean_value(row.get("email"))
            if not email or "@" not in email:
                stats["errors"].append(f"Ligne {index + 2}: email manquant ou invalide.")
                continue

            email = email.lower()
            first_name = clean_value(row.get("first_name"))
            last_name = clean_value(row.get("last_name"))

            if not first_name:
                stats["errors"].append(f"Ligne {index + 2}: prénom manquant.")
                continue
            if not last_name:
                stats["errors"].append(f"Ligne {index + 2}: nom manquant.")
                continue

            # Optionnels
            company_name = clean_value(row.get("company_name"))
            position = clean_value(row.get("position"))
            phone_number = clean_value(row.get("phone_number"))
            base_notes = clean_value(row.get("source_notes"))
            source_notes = build_enriched_notes(row, base_notes)

            # Canal
            canal_raw = clean_value(row.get("canal_raw")) or clean_value(row.get("canal"))
            if canal_raw:
                canal, canal_detail = detect_canal(canal_raw)
            else:
                canal_detail = clean_value(row.get("canal_detail"))
                canal_val = clean_value(row.get("canal"))
                try:
                    canal = ProspectCanal(canal_val) if canal_val else None
                except ValueError:
                    canal = ProspectCanal.other

            source = infer_source_from_canal(canal)

            # Upsert prospect
            existing = db.query(Prospect).filter(
                Prospect.user_id == current_user.id,
                Prospect.email == email
            ).first()

            if existing:
                if update_existing:
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.company_name = company_name
                    existing.position = position
                    existing.phone_number = phone_number
                    existing.source_notes = source_notes
                    existing.canal = canal
                    existing.canal_detail = canal_detail
                    existing.source = source
                    db.flush()
                    prospect_id = existing.id
                    stats["updated"] += 1
                    imported_prospect_ids.append(prospect_id)
                else:
                    stats["skipped"] += 1
                    continue
            else:
                new_prospect = Prospect(
                    user_id=current_user.id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    company_name=company_name,
                    position=position,
                    phone_number=phone_number,
                    source=source,
                    source_notes=source_notes,
                    canal=canal,
                    canal_detail=canal_detail,
                )
                db.add(new_prospect)
                db.flush()
                prospect_id = new_prospect.id
                stats["created"] += 1
                imported_prospect_ids.append(prospect_id)

            # Lien produits (collateral)
            collateral_raw = clean_value(row.get("collateral"))
            if collateral_raw:
                product_ids = find_product_by_collateral(collateral_raw, current_user.id, db)
                for pid in product_ids:
                    already = db.query(ProspectProduct).filter(
                        ProspectProduct.prospect_id == prospect_id,
                        ProspectProduct.product_id == pid,
                    ).first()

                    if not already:
                        db.add(
                            ProspectProduct(
                                prospect_id=prospect_id,
                                product_id=pid,
                                notes=f"Import collateral: {collateral_raw}"
                            )
                        )

        except Exception as e:
            stats["errors"].append(f"Ligne {index + 2}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur commit: {str(e)}")

    # Lier les prospects importés à la campagne si campaign_id fourni
    if campaign_id:
        for pid in imported_prospect_ids:
            already = db.query(CampaignContact).filter(
                CampaignContact.campaign_id == campaign_id,
                CampaignContact.prospect_id == pid,
            ).first()
            if not already:
                db.add(
                    CampaignContact(
                        campaign_id=campaign_id,
                        prospect_id=pid,
                        status="pending",
                    )
                )
        try:
            db.commit()
        except Exception as e:
            db.rollback()
    return {
        "success": True,
        "total_rows": len(df),
        "created": stats["created"],
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "error_count": len(stats["errors"]),
        "errors": stats["errors"][:20],
        "prospect_ids": imported_prospect_ids,
    }


@router.get("/export")
def export_prospects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporte tous les prospects user au format Excel.
    """
    prospects = db.query(Prospect).filter(Prospect.user_id == current_user.id).all()
    if not prospects:
        raise HTTPException(status_code=404, detail="Aucun prospect trouvé pour export.")

    data = [
        {
            "email": p.email,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "company_name": p.company_name,
            "position": p.position,
            "phone_number": p.phone_number,
            "source": p.source.value if p.source else "",
            "canal": p.canal.value if p.canal else "",
            "canal_detail": p.canal_detail or "",
            "status": p.status.value if p.status else "",
            "source_notes": p.source_notes or "",
        }
        for p in prospects
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Prospects")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=prospects_export.xlsx"},
    )