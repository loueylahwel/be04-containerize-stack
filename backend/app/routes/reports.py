from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import settings
from ..auth import get_current_user
from ..reports import run_report_job

router = APIRouter(prefix="/api/reports", tags=["reports"])

_engine = None
_SessionLocal = None


def _get_session():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


class ReportOut(BaseModel):
    id: int
    title: str
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.post("/generate", response_model=ReportOut, status_code=202)
async def generate_report(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        result = session.execute(
            text("INSERT INTO reports (user_id, title, status) VALUES (:uid, :title, 'pending') RETURNING id, created_at"),
            {"uid": current_user["id"], "title": f"Items Report by {current_user['username']}"},
        )
        row = result.fetchone()
        report_id = row[0]
        created_at = str(row[1])
        session.commit()

    background_tasks.add_task(run_report_job, report_id)

    return ReportOut(id=report_id, title=f"Items Report by {current_user['username']}", status="pending", created_at=created_at)


@router.get("/", response_model=list[ReportOut])
async def list_reports(current_user: dict = Depends(get_current_user)):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        rows = session.execute(
            text("SELECT id, title, status, error_message, created_at, completed_at FROM reports WHERE user_id = :uid ORDER BY id DESC"),
            {"uid": current_user["id"]},
        ).fetchall()

    return [
        ReportOut(
            id=r[0], title=r[1], status=r[2], error_message=r[3],
            created_at=str(r[4]) if r[4] else None,
            completed_at=str(r[5]) if r[5] else None,
        )
        for r in rows
    ]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: int, current_user: dict = Depends(get_current_user)):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT id, title, status, error_message, created_at, completed_at FROM reports WHERE id = :id AND user_id = :uid"),
            {"id": report_id, "uid": current_user["id"]},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportOut(
        id=row[0], title=row[1], status=row[2], error_message=row[3],
        created_at=str(row[4]) if row[4] else None,
        completed_at=str(row[5]) if row[5] else None,
    )


@router.get("/{report_id}/download")
async def download_report(report_id: int, current_user: dict = Depends(get_current_user)):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT status, file_path FROM reports WHERE id = :id AND user_id = :uid"),
            {"id": report_id, "uid": current_user["id"]},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    status, file_path = row

    if status == "pending" or status == "running":
        raise HTTPException(status_code=202, detail=f"Report is still {status}")

    if status == "failed":
        raise HTTPException(status_code=500, detail="Report generation failed")

    if not file_path:
        raise HTTPException(status_code=404, detail="PDF file not found")

    import os
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.pdf",
        media_type="application/pdf",
    )
