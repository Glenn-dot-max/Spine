"""
Spine CRM - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import from routes (existing files)
from app.routes.auth import router as auth_router
from app.routes.prospects import router as prospects_router
from app.routes import auth

# Import from api (new OAuth)
from app.api.oauth import router as oauth_router

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
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(prospects_router, prefix="/api/prospects", tags=["prospects"])
app.include_router(oauth_router, prefix="/api/oauth", tags=["oauth"])


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