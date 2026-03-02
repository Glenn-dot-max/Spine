"""
Spine CRM - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, prospects, oauth, emails

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
    allow_origins=["http://localhost:5173"],  # Frontend specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(prospects.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(emails.router, prefix="/api")


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