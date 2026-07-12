from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from pydantic_settings import BaseSettings
from .base import ItemRepository
from ..schemas import ItemCreate, ItemUpdate, ItemOut


class Base(DeclarativeBase):
    pass


class ItemRow(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    description: Mapped[Optional[str]]


class PostgresItemRepository(ItemRepository):
    """Real Postgres storage via SQLAlchemy. Data survives restarts."""

    def __init__(self, database_url: str):
        self._engine = create_engine(database_url, pool_pre_ping=True)
        self._SessionLocal = sessionmaker(bind=self._engine)

    def _to_out(self, row: ItemRow) -> ItemOut:
        return ItemOut(id=row.id, name=row.name, description=row.description)

    async def create(self, item: ItemCreate) -> ItemOut:
        with self._SessionLocal() as session:
            row = ItemRow(name=item.name, description=item.description)
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_out(row)

    async def get_all(self) -> list[ItemOut]:
        with self._SessionLocal() as session:
            rows = session.execute(text("SELECT id, name, description FROM items ORDER BY id")).fetchall()
            return [ItemOut(id=r[0], name=r[1], description=r[2]) for r in rows]

    async def get_by_id(self, item_id: int) -> Optional[ItemOut]:
        with self._SessionLocal() as session:
            row = session.execute(
                text("SELECT id, name, description FROM items WHERE id = :id"),
                {"id": item_id},
            ).fetchone()
            return ItemOut(id=row[0], name=row[1], description=row[2]) if row else None

    async def update(self, item_id: int, item: ItemUpdate) -> Optional[ItemOut]:
        with self._SessionLocal() as session:
            existing = session.execute(
                text("SELECT id, name, description FROM items WHERE id = :id"),
                {"id": item_id},
            ).fetchone()
            if not existing:
                return None
            updates = item.model_dump(exclude_unset=True)
            if updates:
                set_clause = ", ".join(f"{k} = :{k}" for k in updates)
                updates["id"] = item_id
                session.execute(text(f"UPDATE items SET {set_clause} WHERE id = :id"), updates)
                session.commit()
            row = session.execute(
                text("SELECT id, name, description FROM items WHERE id = :id"),
                {"id": item_id},
            ).fetchone()
            return ItemOut(id=row[0], name=row[1], description=row[2])

    async def delete(self, item_id: int) -> bool:
        with self._SessionLocal() as session:
            result = session.execute(text("DELETE FROM items WHERE id = :id"), {"id": item_id})
            session.commit()
            return result.rowcount > 0
