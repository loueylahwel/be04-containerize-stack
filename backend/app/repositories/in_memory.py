import itertools
from typing import Optional
from .base import ItemRepository
from ..schemas import ItemCreate, ItemUpdate, ItemOut


class InMemoryItemRepository(ItemRepository):
    """Dict-based storage. Data is lost on restart — proves persistence when swapped for Postgres."""

    def __init__(self):
        self._store: dict[int, ItemOut] = {}
        self._id_counter = itertools.count(1)

    async def create(self, item: ItemCreate) -> ItemOut:
        item_id = next(self._id_counter)
        saved = ItemOut(id=item_id, **item.model_dump())
        self._store[item_id] = saved
        return saved

    async def get_all(self) -> list[ItemOut]:
        return list(self._store.values())

    async def get_by_id(self, item_id: int) -> Optional[ItemOut]:
        return self._store.get(item_id)

    async def update(self, item_id: int, item: ItemUpdate) -> Optional[ItemOut]:
        existing = self._store.get(item_id)
        if not existing:
            return None
        updated = existing.model_copy(update=item.model_dump(exclude_unset=True))
        self._store[item_id] = updated
        return updated

    async def delete(self, item_id: int) -> bool:
        return self._store.pop(item_id, None) is not None
