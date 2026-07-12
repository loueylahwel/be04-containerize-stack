from abc import ABC, abstractmethod
from typing import Optional
from ..schemas import ItemCreate, ItemUpdate, ItemOut


class ItemRepository(ABC):
    """Abstract interface for item storage. Both in-memory and Postgres repos implement this."""

    @abstractmethod
    async def create(self, item: ItemCreate) -> ItemOut:
        ...

    @abstractmethod
    async def get_all(self) -> list[ItemOut]:
        ...

    @abstractmethod
    async def get_by_id(self, item_id: int) -> Optional[ItemOut]:
        ...

    @abstractmethod
    async def update(self, item_id: int, item: ItemUpdate) -> Optional[ItemOut]:
        ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        ...
