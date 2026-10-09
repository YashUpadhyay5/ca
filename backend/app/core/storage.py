import hashlib
import os
import shutil
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile, HTTPException
from app.config import settings

class StorageManager:
    """Enterprise Storage Manager for PDF Statement files and Excel/Report exports."""

    @staticmethod
    def compute_sha256(file_obj: BinaryIO) -> str:
        """Calculate SHA256 checksum of an uploaded stream."""
        hasher = hashlib.sha256()
        file_obj.seek(0)
        while chunk := file_obj.read(8192):
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()

    @classmethod
    def save_document(cls, file: UploadFile, org_id: str, document_id: str) -> tuple[str, str, int]:
        """
        Securely persists uploaded PDF.
        Returns: (relative_storage_path, sha256_checksum, file_size)
        """
        # Validate extension
        suffix = Path(file.filename).suffix.lower()
        if suffix not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format '{suffix}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Sanitize filename & prevent path traversal
        safe_filename = f"{document_id}{suffix}"
        org_dir = settings.DOCUMENTS_DIR / str(org_id)
        org_dir.mkdir(parents=True, exist_ok=True)
        dest_path = org_dir / safe_filename

        # Write and compute checksum
        hasher = hashlib.sha256()
        file_size = 0

        with open(dest_path, "wb") as buffer:
            while chunk := file.file.read(8192):
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="File exceeds maximum allowed size (50MB).")
                hasher.update(chunk)
                buffer.write(chunk)

        file.file.seek(0)
        rel_path = str(dest_path.relative_to(settings.STORAGE_DIR))
        return rel_path, hasher.hexdigest(), file_size

    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path:
        """Resolves relative storage path to safe absolute Path."""
        full_path = (settings.STORAGE_DIR / relative_path).resolve()
        # Path traversal guard
        if not str(full_path).startswith(str(settings.STORAGE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Illegal file path access attempt.")
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Requested file not found in storage.")
        return full_path

    @classmethod
    def delete_file(cls, relative_path: str) -> bool:
        """Safely removes file from storage."""
        try:
            full_path = cls.get_absolute_path(relative_path)
            full_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False
