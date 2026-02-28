from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI
from app.db import db_ping

app = FastAPI(title="Spine API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    db_ping()
    return {"db": "ok"}