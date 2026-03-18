"""
Script to FORCE reset the database.
This uses raw SQL to ensure all data is deleted.
"""
from sqlalchemy import text
from app.db import engine, SessionLocal

print("🗑️  FORCING database cleanup...")

# Create a connection
with engine.connect() as conn:
    # Start a transaction
    trans = conn.begin()
    
    try:
        # Disable foreign key checks temporarily (PostgreSQL)
        print("   - Disabling constraints...")
        
        # Delete all data in correct order
        print("   - Deleting prospect_products...")
        conn.execute(text("DELETE FROM prospect_products"))
        
        print("   - Deleting prospects...")
        conn.execute(text("DELETE FROM prospects"))
        
        print("   - Deleting products...")
        conn.execute(text("DELETE FROM products"))
        
        print("   - Deleting users...")
        conn.execute(text("DELETE FROM users"))
        
        # Reset ID sequences (PostgreSQL)
        print("   - Resetting ID sequences...")
        conn.execute(text("ALTER SEQUENCE IF EXISTS prospect_products_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE IF EXISTS prospects_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE IF EXISTS products_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1"))
        
        # Commit the transaction
        trans.commit()
        print("✅ All data deleted and sequences reset!")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Error: {e}")
        raise

# Verify
print("\n🔍 Verifying...")
db = SessionLocal()
try:
    from app.models import User, Product, Prospect, ProspectProduct
    
    users_count = db.query(User).count()
    products_count = db.query(Product).count()
    prospects_count = db.query(Prospect).count()
    links_count = db.query(ProspectProduct).count()
    
    print(f"   - Users: {users_count}")
    print(f"   - Products: {products_count}")
    print(f"   - Prospects: {prospects_count}")
    print(f"   - Product Links: {links_count}")
    
    if users_count == 0 and products_count == 0:
        print("\n✅ SUCCESS! Database is now EMPTY!")
    else:
        print("\n❌ FAILED! Database still contains data!")
finally:
    db.close()