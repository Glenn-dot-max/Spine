"""
Check if database is empty
"""
from app.db import SessionLocal
from app.models import User, Product, Prospect, ProspectProduct

db = SessionLocal()

try:
    users_count = db.query(User).count()
    products_count = db.query(Product).count()
    prospects_count = db.query(Prospect).count()
    links_count = db.query(ProspectProduct).count()
    
    print("📊 Database Status:")
    print(f"   - Users: {users_count}")
    print(f"   - Products: {products_count}")
    print(f"   - Prospects: {prospects_count}")
    print(f"   - Product Links: {links_count}")
    print()
    
    if users_count == 0 and products_count == 0 and prospects_count == 0 and links_count == 0:
        print("✅ Database is EMPTY!")
    else:
        print("⚠️  Database contains data!")
        
finally:
    db.close()