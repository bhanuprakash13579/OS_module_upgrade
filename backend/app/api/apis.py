"""
COPS ↔ APIS Module API.

POST /api/apis/match   — upload an APIS Excel, get JSON results
POST /api/apis/export  — upload an APIS Excel, get a formatted .xlsx download
"""
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.services.apis_match import match_from_excel, export_to_excel

router = APIRouter()

_MAX_FILE_SIZE = 20 * 1024 * 1024   # 20 MB safety cap


def _read_upload(file: UploadFile) -> bytes:
    data = file.file.read(_MAX_FILE_SIZE + 1)
    if len(data) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 20 MB.",
        )
    return data


@router.post("/match")
def apis_match(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload an APIS Excel file (.xlsx).
    Returns JSON with every matched passenger, their COPS cases and items.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel file (.xlsx or .xls).",
        )

    raw = _read_upload(file)

    try:
        result = match_from_excel(raw, db)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process Excel file: {e}",
        )

    return result


@router.post("/export")
def apis_export(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload an APIS Excel file (.xlsx).
    Returns a formatted .xlsx report of all matched passengers / cases.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel file (.xlsx or .xls).",
        )

    raw = _read_upload(file)

    try:
        result   = match_from_excel(raw, db)
        xlsx_bytes = export_to_excel(result)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to generate report: {e}",
        )

    filename = f"COPS_APIS_Match_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx"
    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
