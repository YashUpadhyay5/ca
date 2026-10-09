from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.database import init_db, SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.client import Client
from app.models.bank_account import BankAccount
from app.core.security import get_password_hash

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.clients import router as clients_router
from app.api.v1.documents import router as documents_router
from app.api.v1.statements import router as statements_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.review import router as review_router
from app.api.v1.exports import router as exports_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.audit import router as audit_router

def seed_initial_demo_firm():
    """Seeds default CA Firm and sample client if database is brand new."""
    db = SessionLocal()
    try:
        user_cnt = db.query(User).count()
        if user_cnt == 0:
            org = Organization(
                name="K. R. Mehta & Associates, Chartered Accountants",
                pan="AABCK1234F",
                gstin="27AABCK1234F1Z5"
            )
            db.add(org)
            db.flush()

            admin_user = User(
                org_id=org.id,
                email="ca@mehtaca.com",
                hashed_password=get_password_hash("AuditPassword123!"),
                full_name="CA Rajesh Mehta, FCA",
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        print(f"Seed note: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed CA firm
    init_db()
    seed_initial_demo_firm()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production Bank Statement PDF Intelligence, Conversion, Analysis & Reconciliation Platform for CA Firms",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication & Organizations"])
app.include_router(clients_router, prefix=f"{settings.API_V1_STR}/clients", tags=["Clients & Bank Accounts"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents & Upload"])
app.include_router(statements_router, prefix=f"{settings.API_V1_STR}/statements", tags=["Statements & Transactions"])
app.include_router(transactions_router, prefix=f"{settings.API_V1_STR}/transactions", tags=["Transaction Operations & Edits"])
app.include_router(review_router, prefix=f"{settings.API_V1_STR}/review", tags=["Review Queue & Verification"])
app.include_router(exports_router, prefix=f"{settings.API_V1_STR}/exports", tags=["Excel & CSV Exports"])
app.include_router(assistant_router, prefix=f"{settings.API_V1_STR}/assistant", tags=["Natural Language CA Assistant"])
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit", tags=["Audit Logs"])

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "platform": settings.PROJECT_NAME,
        "engine": "FastAPI + PyMuPDF + RapidOCR + openpyxl",
        "precision": "Decimal (Accounting-Safe)"
    }

# Mount frontend production build if available
from fastapi.staticfiles import StaticFiles
from pathlib import Path
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

