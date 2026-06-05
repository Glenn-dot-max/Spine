"""
Product import routes - Upload Excel/CSV files to bulk import products into the system.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import io
from typing import List

from app.db import get_db
from app.models.user import User
from app.models.product import Product
from app.schemas import ProductImportResult, ProductImportPreview, PDFImportPreview
from app.api.deps import get_current_user
from app.services.pdf_ai_extractor import extract_products_with_ai

router = APIRouter(prefix="/api/products", tags=["product-import"])

@router.get("/import/template")
async def download_import_template():
    """
    Download Excel template for product import.
    
    Returns an Excel file with correct columns and example data.
    Fill this template and upload via POST /api/products/import
    """
    from fastapi.responses import StreamingResponse

    # Create template with all food distribution fields + example rows
    df = pd.DataFrame({
        'item_number':    ['CLOV-MUS-IBC', 'CLOV-VIN-5L', 'CLOV-BAL-1L'],
        'name':           ['Clovis Dijon Mustard IBC', 'Clovis White Vinegar 5L', 'Clovis Balsamic 1L'],
        'brand':          ['Clovis', 'Clovis', 'Clovis'],
        'short_description': [
            'Industrial grade Dijon mustard in IBC tote',
            'White wine vinegar for foodservice',
            'Premium balsamic vinegar retail format'
        ],
        'category':       ['mustard', 'vinegar', 'balsamic'],
        'formats':        ['IBC 1000L, drum 200L', '5L bottle, 10L bag-in-box', '1L bottle, case of 12'],
        'price_range':    ['$2.20-$2.60/kg', '$1.80-$2.10/L', '$4.50-$5.20/L'],
        'certifications': ['Kosher, Non-GMO', 'Organic, Kosher', 'Organic'],
        'segments':       ['industry, foodservice', 'foodservice, retail', 'retail, foodservice'],
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

        instructions = pd.DataFrame({
            'Column': [
                'item_number ✅ REQUIRED',
                'name ✅ REQUIRED',
                'brand',
                'short_description',
                'category',
                'formats',
                'price_range',
                'certifications',
                'segments',
            ],
            'Description': [
                'Unique product code / SKU',
                'Full product name',
                'Brand name',
                'Short product description',
                'Product category: mustard / vinegar / balsamic / crepes / other',
                'Available formats, comma-separated: "IBC 1000L, drum 200L, 5L bottle"',
                'Price range: "$2.20-$2.60/kg"',
                'Certifications comma-separated: "Organic, Kosher, Non-GMO"',
                'Target segments comma-separated: "industry, foodservice, retail"',
            ],
            'Example': [
                'CLOV-MUS-IBC',
                'Clovis Dijon Mustard IBC',
                'Clovis',
                'Industrial grade Dijon mustard',
                'mustard',
                'IBC 1000L, drum 200L',
                '$2.20-$2.60/kg',
                'Kosher, Non-GMO',
                'industry, foodservice',
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name='Instructions')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": "attachment; filename=product_import_template.xlsx"  
        }
    )

@router.post("/import/preview", response_model=ProductImportPreview)
async def preview_product_import(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Preview Excel/CSV file before importing.
    Returns first 10 rows and validation warnings.

    Excpected columns:
    - item_number (required)
    - name (required)
    - description (optional)
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(400, "File must be CSV or Excel format")
    
    contents = await file.read()

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Error reading file: {str(e)}")
    
    # Validate required columns
    required_columns = {'item_number', 'name'}
    missing = [col for col in required_columns if col not in df.columns]

    warnings = []
    if missing:
        warnings.append(f"❌ Missing required columns: {', '.join(missing)}")
        warnings.append("Required: item_number, name")
        warnings.append("Optional: description")
    else:
        # Check for empty rows
        empty_rows = df[df['item_number'].isna()].index.tolist()
        if empty_rows:
            warnings.append(f"⚠️ Found {len(empty_rows)} rows with empty item_number (will be skipped)")

        # Check for duplicates in the file
        duplicates = df[df.duplicated(subset=['item_number'], keep=False)]
        if not duplicates.empty:
            dup_items = duplicates['item_number'].unique().tolist()[:5]
            warnings.append(f"⚠️ Found duplicate item_numbers in file: {dup_items}")
        
        if not warnings:
            warnings.append("✅ File looks good! No issues found.")

    return ProductImportPreview(
        sample_data=df.head(10).fillna("").to_dict('records'),
        total_rows=len(df),
        columns_detected=list(df.columns),
        warnings=warnings
    )

@router.post("/import", response_model=ProductImportResult)
async def import_products(
    file: UploadFile = File(...),
    update_existing: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Import products from Excel/CSV file.

    Parameters:
    - file: Excel/CSV file containing product data.
    - update_existing: if True, updates existing products with same item_number

    Excpected columns:
    - item_number (required)
    - name (required)
    - description (optional)
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(400, "File must be CSV or Excel format")
    
    contents = await file.read()

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Error reading file: {str(e)}")
    
    # Validate required columns
    if 'item_number' not in df.columns or 'name' not in df.columns:
        raise HTTPException(400, "File must contain 'item_number' and 'name' columns")
    
    created = 0
    updated = 0
    skipped = 0
    errors = []

    for index, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row['item_number']) or pd.isna(row['name']):
                skipped += 1
                continue
            
            item_number = str(row['item_number']).strip()
            name = str(row['name']).strip()

            # Check if product already exists
            existing = db.query(Product).filter(
                Product.user_id == user.id,
                Product.item_number == item_number
            ).first()

            if existing:
                if update_existing:
                    # Update existing product
                    def get_field(field):
                        return str(row[field]).strip() if field in row and pd.notna(row[field]) else None
                    
                    existing.name = name
                    for field in ['brand', 'category', 'formats', 'price_range', 'certifications', 'segments']:
                        value = get_field(field)
                        if value is not None:
                            setattr(existing, field, value)                    
                    updated += 1
                else:
                    # Skip existing product
                    errors.append({
                        "row": index + 2,
                        "item_number": item_number,
                        "error": "Product with this item_number already exists (set update_existing=True to update)"
                    })
                    skipped += 1
            else:
                # Create new product
                def get_field(field):
                    return str(row[field]).strip() if field in row and pd.notna(row[field]) else None
                
                new_product = Product(
                    user_id=user.id,
                    item_number=item_number,
                    name=name,
                    brand=get_field('brand'),
                    short_description=get_field('short_description'),
                    category=get_field('category'),
                    formats=get_field('formats'),
                    price_range=get_field('price_range'),
                    certifications=get_field('certifications'),
                    segments=get_field('segments'),
                )
                db.add(new_product)
                created += 1

        except Exception as e:
            errors.append({
                "row": index + 2,
                "item_number": row.get('item_number', 'N/A'),
                "error": str(e)
            })
            skipped += 1

    # Commit all changes to the database
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error saving to database: {str(e)}")
    
    return ProductImportResult(
        total_rows=len(df),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors
    )

@router.get("/export")
async def export_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Export all products to Excel.
    Useful for backup or editing in Excel before re-importing.
    """
    from fastapi.responses import StreamingResponse

    products = db.query(Product).filter(Product.user_id == user.id).all()

    if not products:
        raise HTTPException(404, "No products found to export")
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        "item_number": p.item_number,
        "name": p.name,
        "short_description": p.short_description
    } for p in products])

    # Create Excel file in memory
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Products')
    output.seek(0)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": f"attachment; filename=products_export.xlsx"
        }
    )

@router.post("/import/pdf/preview", response_model=PDFImportPreview)
async def preview_pdf_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Preview PDF catalog extraction via Haiku Vision avant import.
    Retourne les produits détectés sans les sauvegarder en base.
    Le frontend peut alors confirmer ou corriger avant l'import définitif.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")
    
    contents = await file.read()
    warnings = []

    try:
        extracted = extract_products_with_ai(contents)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Extraction error: {str(e)}")
    

    # Détecter le mode utilisé (texte ou vision) pour l'afficher dans l'UI
    import io as _io
    import pdfplumber as _pdfplumber
    raw_text = ""
    try:
        with _pdfplumber.open(_io.BytesIO(contents)) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    raw_text += t
    except Exception:
        num_pages = 1

    avg_chars = len(raw_text) / max(num_pages, 1)
    extraction_mode = "text" if avg_chars >= 100 else "vision"

    if num_pages > 15:
        warnings.append(f"⚠️ This PDF has {num_pages} pages.")

    if not extracted:
        warnings.append("⚠️ No products could be extracted from this PDF. Try importing a CSV instead.")
    
    return PDFImportPreview(
        products=[p.model_dump() for p in extracted],
        total_extracted=len(extracted),
        extraction_mode=extraction_mode,
        warnings=warnings
    )


@router.post("/import/pdf", response_model=ProductImportResult)
async def import_products_from_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Import products from a PDF catalog.
    Automatically extracts tables and product lines from the PDF.
    The file is NOT stored - processed in memory only.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")
    
    contents = await file.read()

    try:
        extracted_products = extract_products_with_ai(contents)
        # Convertir en dicts pour la suite du traitement existant
        extracted = [p.model_dump() for p in extracted_products]
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")
    
    if not extracted:
        raise HTTPException(400, "No products could be extracted from this PDF. Try importing a CSV instead.")
    
    created = 0
    updated = 0
    skipped = 0
    errors = []

    for item in extracted:
        try:
            item_number = item.get('item_number', '').strip()
            name = item.get('name', '').strip()

            if not item_number or not name:
                skipped += 1
                continue
            
            # Check if product already exists
            existing = db.query(Product).filter(
                Product.user_id == user.id,
                Product.item_number == item_number
            ).first()

            if existing:
                skipped += 1
            else:
                new_product = Product(
                    user_id=user.id,
                    item_number=item_number,
                    name=name,
                    brand=item.get('brand'),
                    short_description=item.get('short_description'),
                    category=item.get('category'),
                    formats=item.get('formats'),
                    price_range=item.get('price_range'),
                    certifications=item.get('certifications'),
                    segments=item.get('segments'),
                )
                db.add(new_product)
                created += 1

        except Exception as e:
            errors.append({'item_number': item.get('item_number', 'N/A'), "error": str(e)})
            skipped += 1

    db.commit()

    return ProductImportResult(
        total_rows=len(extracted),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors
    )
