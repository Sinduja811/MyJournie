# src/backend/routers/memory_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional
from pydantic import BaseModel

from src.backend.memory import create_prod_memory_store, MemoryStore, SessionLocal

router = APIRouter(prefix="/memory", tags=["memory"])

# Pydantic models for API
class MemoryAddIn(BaseModel):
    role: str
    content: str
    tags: Optional[List[str]] = None

class MemoryOut(BaseModel):
    id: str
    user_id: str
    timestamp: Optional[str]
    role: str
    content: str
    tags: List[str] = []

# instantiate store (singleton for app)
_store: MemoryStore = create_prod_memory_store()

# Dependency (if you want to inject different store per app instance later)
def get_store() -> MemoryStore:
    return _store

@router.post("/{user_id}", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
def add_memory(user_id: str, payload: MemoryAddIn, store: MemoryStore = Depends(get_store)):
    entry = store.add_memory(user_id=user_id, role=payload.role, content=payload.content, tags=payload.tags)
    return entry

@router.get("/{user_id}", response_model=List[MemoryOut])
def list_memory(user_id: str, limit: Optional[int] = Query(None, ge=1), include_archive: bool = Query(False), store: MemoryStore = Depends(get_store)):
    result = store.get_memory(user_id=user_id, limit=limit, include_archive=include_archive)
    return result

@router.get("/{user_id}/search", response_model=List[MemoryOut])
def search_memory(user_id: str, q: str = Query(..., min_length=1), include_archive: bool = Query(False), limit: int = Query(50), store: MemoryStore = Depends(get_store)):
    hits = store.search_memory(user_id=user_id, query=q, include_archive=include_archive, limit=limit)
    return hits

@router.get("/info")
def memory_info(store: MemoryStore = Depends(get_store)):
    # Protect this endpoint in prod (admin-only)
    return store.info()

@router.get("/{user_id}/relevant", response_model=List[MemoryOut])
def get_relevant(user_id: str, k: int = Query(5, ge=1, le=200), store: MemoryStore = Depends(get_store)):
    return store.get_relevant_memory(user_id=user_id, recent_k=k)
