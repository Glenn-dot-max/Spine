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
from app.schemas import ProductImportResult, ProductImportPreview
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])

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
                    existing.name = name
                    if 'short_description' in row and pd.notna(row['short_description']):
                        existing.short_description = str(row['short_description']).strip()
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
                new_product = Product(
                    user_id=user.id,
                    item_number=item_number,
                    name=name,
                    short_description=str(row['short_description']).strip() if 'short_description' in row and pd.notna(row['short_description']) else None
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

    