from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from ..schemas import ItemCreate, ItemUpdate, ItemOut
from ..repositories.base import ItemRepository

router = APIRouter(prefix="/api/items", tags=["items"])

_repository: ItemRepository | None = None


def set_repository(repo: ItemRepository):
    global _repository
    _repository = repo


def get_repository() -> ItemRepository:
    if _repository is None:
        raise RuntimeError("Repository not initialized")
    return _repository


@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(item: ItemCreate, repo: ItemRepository = Depends(get_repository)):
    return await repo.create(item)


@router.get("/", response_model=list[ItemOut])
async def list_items(repo: ItemRepository = Depends(get_repository)):
    return await repo.get_all()


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int, repo: ItemRepository = Depends(get_repository)):
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(item_id: int, item: ItemUpdate, repo: ItemRepository = Depends(get_repository)):
    updated = await repo.update(item_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, repo: ItemRepository = Depends(get_repository)):
    deleted = await repo.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
