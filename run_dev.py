import uvicorn
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("=" * 70)
    print("   CaFinIQ — Production CA Bank Statement Intelligence Platform")
    print("=" * 70)
    print(" * Serving Full-Stack App: http://localhost:8000")
    print(" * Interactive API Docs:  http://localhost:8000/docs")
    print(" * Default Seed CA Login: ca@mehtaca.com / AuditPassword123!")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, app_dir=str(backend_dir), reload=True)
