import os
from sqlalchemy import create_engine, text

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(database_url, echo=True)

def db_ping():
    """Teste la connexion à la base de données"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        result.fetchone()
    return {"db": "ok"}