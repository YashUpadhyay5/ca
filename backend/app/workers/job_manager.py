import threading
import uuid
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.review import ReviewItem
from app.models.audit_log import AuditLog
from app.core.storage import StorageManager
from app.extraction.pipeline import ExtractionPipeline

class JobManager:
    """In-memory and persistent background job coordinator for statement extraction."""

    _jobs: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def create_job(cls, document_id: str) -> str:
        job_id = str(uuid.uuid4())
        with cls._lock:
            cls._jobs[job_id] = {
                "job_id": job_id,
                "document_id": document_id,
                "status": "QUEUED",
                "progress_percentage": 0,
                "current_step": "Queued for extraction",
                "pages_processed": 0,
                "total_pages": 0,
                "transactions_extracted": 0,
                "high_confidence_pct": 100.0,
                "review_required_count": 0,
                "error_message": None,
                "statement_id": None,
                "created_at": datetime.now(timezone.utc)
            }
        return job_id

    @classmethod
    def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            return cls._jobs.get(job_id)

    @classmethod
    def update_job(cls, job_id: str, **kwargs):
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id].update(kwargs)

    @classmethod
    def start_processing_task(cls, job_id: str, document_id: str, password: Optional[str] = None):
        """Spawns worker thread for PDF extraction with optional decryption password."""
        thread = threading.Thread(target=cls._worker_run, args=(job_id, document_id, password), daemon=True)
        thread.start()

    @classmethod
    def _worker_run(cls, job_id: str, document_id: str, password: Optional[str] = None):
        db = SessionLocal()
        try:
            doc_record = db.query(Document).filter(Document.id == document_id).first()
            if not doc_record:
                cls.update_job(job_id, status="FAILED", error_message="Document record not found.")
                return

            doc_record.status = "PROCESSING"
            db.commit()

            abs_file_path = StorageManager.get_absolute_path(doc_record.storage_path)

            def progress_hook(step: str, pct: int):
                cls.update_job(job_id, current_step=step, progress_percentage=pct)

            cls.update_job(job_id, status="EXTRACTING", progress_percentage=10, current_step="Reading PDF structure")

            # Execute pipeline
            result = ExtractionPipeline.process_pdf(str(abs_file_path), password=password, progress_callback=progress_hook)

            cls.update_job(job_id, current_step="Persisting structured financial dataset", progress_percentage=92)

            # Update Document metadata
            doc_record.page_count = result["total_pages"]
            doc_record.is_scanned = result["is_scanned"]
            doc_record.status = "COMPLETED"

            # Create Statement record
            statement = Statement(
                document_id=doc_record.id,
                bank_name=result["bank_name"],
                account_number_detected=result["account_number"],
                period_start=result["period_start"],
                period_end=result["period_end"],
                opening_balance=result["opening_balance"],
                closing_balance=result["closing_balance"],
                calculated_closing_balance=result["calculated_closing_balance"],
                balance_discrepancy=result["balance_discrepancy"],
                reconciliation_status=result["reconciliation_status"],
                total_transactions=result["total_transactions"],
                total_credits=result["total_credits"],
                total_debits=result["total_debits"],
                net_movement=result["net_movement"],
                parser_used=result["parser_used"],
                confidence_avg=result["confidence_avg"]
            )
            db.add(statement)
            db.flush()

            # If client name was auto-detected, update client record
            if result.get("customer_name") and doc_record.client:
                if doc_record.client.name in ["Client Account", "Primary Client Account", ""]:
                    doc_record.client.name = result["customer_name"]

            # Record bank account if detected
            if result.get("account_number") and doc_record.client:
                from app.models.bank_account import BankAccount
                existing_acc = db.query(BankAccount).filter(
                    BankAccount.client_id == doc_record.client_id,
                    BankAccount.account_number_masked == result["account_number"]
                ).first()
                if not existing_acc:
                    new_acc = BankAccount(
                        client_id=doc_record.client_id,
                        bank_name=result["bank_name"],
                        account_number_masked=result["account_number"],
                        account_type="Current",
                        branch="Auto-detected"
                    )
                    db.add(new_acc)


            # Batch insert transactions
            db_txns = []
            for t_dict in result["transactions"]:
                txn = Transaction(
                    statement_id=statement.id,
                    transaction_date=t_dict["transaction_date"],
                    value_date=t_dict["value_date"],
                    narration=t_dict["narration"],
                    raw_text=t_dict["raw_text"],
                    reference_number=t_dict["reference_number"],
                    cheque_number=t_dict["cheque_number"],
                    debit_amount=t_dict["debit_amount"],
                    credit_amount=t_dict["credit_amount"],
                    balance=t_dict["balance"],
                    payment_mode=t_dict["payment_mode"],
                    category=t_dict["category"],
                    subcategory=t_dict["subcategory"],
                    counterparty=t_dict["counterparty"],
                    upi_id=t_dict["upi_id"],
                    source_page=t_dict["source_page"],
                    source_row=t_dict["source_row"],
                    confidence_score=t_dict["confidence_score"],
                    validation_status=t_dict["validation_status"],
                    is_internal_transfer=t_dict["is_internal_transfer"],
                    is_potential_duplicate=t_dict["is_potential_duplicate"],
                    is_anomaly=t_dict["is_anomaly"],
                    notes=t_dict["notes"]
                )
                db_txns.append(txn)

            db.bulk_save_objects(db_txns)
            db.flush()

            # Insert Review Items
            # Re-query saved transactions to get their generated IDs
            saved_txns = db.query(Transaction).filter(Transaction.statement_id == statement.id).order_by(Transaction.transaction_date).all()
            db_reviews = []
            for rev in result["review_items"]:
                t_idx = rev["transaction_index"]
                if 0 <= t_idx < len(saved_txns):
                    t_obj = saved_txns[t_idx]
                    review_item = ReviewItem(
                        transaction_id=t_obj.id,
                        issue_code=rev["issue_code"],
                        issue_description=rev["issue_description"],
                        status="PENDING"
                    )
                    db_reviews.append(review_item)

            if db_reviews:
                db.bulk_save_objects(db_reviews)

            # Record Audit Log
            audit = AuditLog(
                org_id=doc_record.org_id,
                user_id=None,
                action="PROCESS_DOCUMENT",
                entity_name="Statement",
                entity_id=statement.id,
                details=f"Extracted {len(db_txns)} transactions using {result['parser_used']}. Status: {result['reconciliation_status']}."
            )
            db.add(audit)
            db.commit()

            high_conf_count = sum(1 for t in result["transactions"] if t["confidence_score"] >= 0.90)
            high_conf_pct = (high_conf_count / len(result["transactions"]) * 100) if result["transactions"] else 100.0

            cls.update_job(
                job_id,
                status="COMPLETED",
                progress_percentage=100,
                current_step="Extraction, normalization, and validation complete.",
                pages_processed=result["total_pages"],
                total_pages=result["total_pages"],
                transactions_extracted=len(db_txns),
                high_confidence_pct=round(high_conf_pct, 1),
                review_required_count=len(db_reviews),
                statement_id=statement.id
            )

        except Exception as e:
            traceback.print_exc()
            db.rollback()
            raw_err = str(e)
            error_code = None
            if "PASSWORD_REQUIRED" in raw_err:
                error_code = "PASSWORD_REQUIRED"
                user_msg = "Statement PDF is password protected. Please provide statement password."
            elif "INVALID_PASSWORD" in raw_err:
                error_code = "INVALID_PASSWORD"
                user_msg = "Incorrect statement password. Please verify and try again."
            else:
                error_code = "EXTRACTION_ERROR"
                user_msg = f"Extraction failure: {raw_err}"

            if doc_record:
                doc_record.status = "PASSWORD_REQUIRED" if error_code == "PASSWORD_REQUIRED" else "FAILED"
                doc_record.error_message = user_msg
                db.commit()
            cls.update_job(
                job_id,
                status="FAILED",
                progress_percentage=100,
                current_step="Failed",
                error_message=user_msg,
                error_code=error_code
            )
        finally:
            db.close()
