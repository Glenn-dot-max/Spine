"""
Prospect Import/Export Routes
Allows bulk import and export of prospects via Excel files.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd
import io

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.prospect import Prospect

# Create router
router = APIRouter(prefix="/api/prospects", tags=["prospect-import"])

@router.get("/import/template")
def download_prospect_template():
    """
    Download Excel template for prospect import.
    
    Template includes:
    - email (required, unique)
    - first_name (required)
    - last_name (required)
    - company (optional)
    - job_title (optional)
    - phone (optional)
    - notes (optional)
    """
    # Données d'exemple pour montrer le format
    example_data = {
        'email': [
            'john.doe@restaurant-legourmet.com',
            'marie.martin@bistro-paris.fr',
            'david.chen@kitchen-supply.com'
        ],
        'first_name': ['John', 'Marie', 'David'],
        'last_name': ['Doe', 'Martin', 'Chen'],
        'company': ['Le Gourmet Restaurant', 'Bistro Paris', 'Kitchen Supply Co.'],
        'job_title': ['Chef', 'Owner', 'Purchasing Manager'],
        'phone': ['+33 1 23 45 67 89', '+1 555 123 4567', '+86 10 1234 5678'],
        'notes': [
            'Met at Show Chefs LA 2025 - interested in our new knife series',
            'Visited our stand twice - wants demo of equipment',
            'Requested pricing for bulk order'
        ]
    }

    # Créer un DataFrame pandas
    df = pd.DataFrame(example_data)

    # Créer un fichier excel en mémoire
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Prospects')
    
    # Revenir au début du fichier
    output.seek(0)

    # Préparer les headers HTTP pour le téléchargement
    headers = {
        "Content-Disposition": "attachment; filename=prospect_import_template.xlsx"
    }

    # Retourner le fichier en streaming
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

@router.post("/import/preview")
async def preview_prospect_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview prospect data before importing.
    Shows sample data and validation warnings.
    """
    # 1. Vérifier le type de fichier 
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
      # 2. Lire le fichier Excel
      contents = await file.read()
      df = pd.read_excel(io.BytesIO(contents))

      # 3. Colonnes requises
      required_columns = ['email', 'first_name', 'last_name']
      missing_columns = [col for col in required_columns if col not in df.columns]

      if missing_columns:
          raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_columns)}")
      
      # 4. Nettoyer les données
      for col in df.columns:
          if df[col].dtype == 'object':
              df[col] = df[col].astype(str).str.strip()
      
      # 5. Détecter les problèmes potentiels
      warnings = []

      # A. emails vides
      empty_emails = df[df['email'].isna() | (df['email'] == '') | (df['email'] == 'nan')].shape[0]
      if empty_emails > 0:
          warnings.append(f"⚠️  Found {empty_emails} rows with empty email.")

      # B. Emails invalides
      df['email'] = df['email'].astype(str)
      invalid_emails = df[~df['email'].str.contains('@', na=False)].shape[0]
      if invalid_emails > 0:
          warnings.append(f"⚠️  Found {invalid_emails} rows with invalid email format.")

      # C. Doublons dans le fichier
      duplicate_emails = df[df['email'].duplicated(keep=False)].shape[0]
      if duplicate_emails > 0:
          warnings.append(f"⚠️  Found {duplicate_emails} duplicate emails in the file.")

      # D. Champs first_name et last_name vides
      empty_names = df[
          (df['first_name'].isna() | (df['first_name'] == '') | (df['first_name'] == 'nan')) |
          (df['last_name'].isna() | (df['last_name'] == '') | (df['last_name'] == 'nan'))
      ].shape[0]
      if empty_names > 0:
          warnings.append(f"⚠️  Found {empty_names} rows with empty first_name or last_name.")

      # 6. Préparer l'aperçu (5 premières lignes)
      sample_data = df.head(5).fillna('').to_dict('records')

      # 7. Message si tout est OK
      if not warnings:
          warnings.append("✅ File looks good! No issues found.")

      # 8. Retourner le résultat
      return {
          "sample_data": sample_data,
          "total_rows": len(df),
          "columns_detected": list(df.columns),
          "warnings": warnings
      }
    
    except Exception as e:
      raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
@router.post("/import")
async def import_prospects(
    file: UploadFile = File(...),
    update_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import prospects from Excel file.

    Args:
    - file: Excel file containing prospect data.
    - update_existing: Whether to update existing prospects.
    - current_user: The user performing the import.
    - db: Database session.
    Returns:
    - Summary of import results, including counts of new and updated prospects, and any errors.
    """
    # 1. Vérifier le type de fichier
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        # 2. Lire le fichier Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # 3. Vérifier les colonnes requises
        required_columns = ['email', 'first_name', 'last_name']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_columns)}")
        
        # 4. Nettoyer les données
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()

        # 5. Statistiques d'import
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        # 6. Traiter chaque ligne
        for index, row in df.iterrows():
            try:
                # A. Valider l'email
                email = str(row['email']).strip().lower()

                if not email or email == 'nan' or '@' not in email:
                    stats['errors'].append(f"Row {index + 2}: Invalid or empty email.")                  
                    continue
                
                # B. Valider first_name et last_name
                first_name = str(row['first_name']).strip()
                last_name = str(row['last_name']).strip()

                if not first_name or first_name == 'nan':
                    stats['errors'].append(f"Row {index + 2}: Empty first_name.")
                    continue
                if not last_name or last_name == 'nan':
                    stats['errors'].append(f"Row {index + 2}: Empty last_name.")
                    continue
                
                # C. Chercher si le prospect existe déjà
                existing_prospect = db.query(Prospect).filter(
                    Prospect.email == email,
                    Prospect.user_id == current_user.id
                ).first()

                # D. Préparer les champs optionnels
                company = str(row.get('company', '')).strip() if 'company' in row else None
                if company == 'nan' or company == '':
                    company = None

                job_title = str(row.get('job_title', '')).strip() if 'job_title' in row else None
                if job_title == 'nan' or job_title == '':
                    job_title = None

                phone = str(row.get('phone', '')).strip() if 'phone' in row else None
                if phone == 'nan' or phone == '':
                    phone = None
                
                notes = str(row.get('notes', '')).strip() if 'notes' in row else None
                if notes == 'nan' or notes == '':
                    notes = None

                # E. Logique de création ou mise à jour
                if existing_prospect:
                    if update_existing:
                        existing_prospect.first_name = first_name
                        existing_prospect.last_name = last_name
                        existing_prospect.company = company
                        existing_prospect.job_title = job_title
                        existing_prospect.phone = phone
                        existing_prospect.notes = notes
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    new_prospect = Prospect(
                        user_id=current_user.id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        company=company,
                        job_title=job_title,
                        phone=phone,
                        notes=notes
                    )
                    db.add(new_prospect)
                    stats['created'] += 1

            except Exception as e:
                stats['errors'].append(f"Row {index + 2}: {str(e)}")
                
        # 7. Commit des changements
        db.commit()

        # 8. Retourner le résumé de l'import
        return {
            "success": True,
            "total_rows": len(df),
            "created": stats['created'],
            "updated": stats['updated'],
            "skipped": stats['skipped'],
            "error_count": len(stats['errors']),
            "errors": stats['errors'][:10]
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
@router.get("/export")
def export_prospects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export prospects to Excel file.
    """
    try:
        # 1. Récupérer les prospects de l'utilisateur
        prospects = db.query(Prospect).filter(Prospect.user_id == current_user.id).all()

        if not prospects:
            raise HTTPException(status_code=404, detail="No prospects found to export.")

        # 2. Convertir en DataFrame pandas
        data = []
        for p in prospects:
            data.append({
                "email": p.email,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "company": p.company,
                "job_title": p.job_title,
                "phone": p.phone,
                "notes": p.notes
            })
        
        df = pd.DataFrame(data)

        # 3. Créer un fichier excel en mémoire
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Prospects')
        
        output.seek(0)

        # 4. Préparer les headers HTTP pour le téléchargement
        headers = {
            "Content-Disposition": "attachment; filename=prospects_export.xlsx"
        }

        # 5. Retourner le fichier en streaming
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting prospects: {str(e)}")