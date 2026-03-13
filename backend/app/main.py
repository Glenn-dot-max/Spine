"""
Spine CRM - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the main API router (contains all sub-routers)
from app.routes import api_router
from app.api.oauth import router as oauth_router
from app.routes import auth, prospects, products, campaigns

# Create FastAPI app
app = FastAPI(
    title="Spine CRM API",
    description="Email automation CRM for prospect management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)  # ← Inclut TOUS les routers (auth, products, import, prospects, etc.)
app.include_router(oauth_router, prefix="/api/oauth", tags=["oauth"])
app.include_router(campaigns.router, prefix="/api")


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "message": "Spine CRM API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check for monitoring."""
    return {"status": "healthy"}