from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.statement import Statement
from app.calculations.query_assistant import SafeQueryAssistant
from app.api.deps import get_current_user

router = APIRouter()

class AssistantQueryRequest(BaseModel):
    statement_id: str
    query: str

@router.post("/query")
def ask_assistant(
    req: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Answers natural language financial queries using validated AST filters without arbitrary SQL injection."""
    statement = db.query(Statement).join(Document).filter(
        Statement.id == req.statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    res = SafeQueryAssistant.answer_query(db, req.statement_id, req.query)
    return res
