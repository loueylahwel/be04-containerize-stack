import logging
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import settings
from .pdf_generator import generate_items_report

logger = logging.getLogger("reports")

_engine = None
_SessionLocal = None
_output_dir = "/app/output"


def _get_session():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


def run_report_job(report_id: int):
    """Background job: query data, generate PDF, update status."""
    SessionLocal = _get_session()
    os.makedirs(_output_dir, exist_ok=True)

    try:
        with SessionLocal() as session:
            session.execute(text("UPDATE reports SET status = 'running' WHERE id = :id"), {"id": report_id})
            session.commit()

        with SessionLocal() as session:
            rows = session.execute(
                text("SELECT id, name, description FROM items ORDER BY id")
            ).fetchall()

        items = [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]

        file_name = f"report_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(_output_dir, file_name)

        generate_items_report(file_path, items, report_title=f"Items Report #{report_id}")

        with SessionLocal() as session:
            session.execute(
                text("UPDATE reports SET status = 'completed', file_path = :path, completed_at = NOW() WHERE id = :id"),
                {"id": report_id, "path": file_path},
            )
            session.commit()

        logger.info("report %d completed → %s (%d items)", report_id, file_path, len(items))

    except Exception as e:
        logger.error("report %d failed: %s", report_id, e)
        with SessionLocal() as session:
            session.execute(
                text("UPDATE reports SET status = 'failed', error_message = :err WHERE id = :id"),
                {"id": report_id, "err": str(e)},
            )
            session.commit()
