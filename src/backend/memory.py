# src/backend/memory.py
"""
MemoryStore for MyJournie.

- Uses SQLAlchemy ORM (sync) and supports SQLite (dev) and PostgreSQL (prod).
- Hybrid memory: active table + archive table.
- Automatic tagging via injected tagger callables.
- Export / import utilities.
- Retention and automatic archival when per-user active count exceeds max_active_per_user.

Usage:
    from src.backend.memory import MemoryStore, get_db_session
    store = MemoryStore(max_active_per_user=500, archive_batch_size=100)
    store.add_memory(user_id="user_1", role="user", content="I feel sad today")
    recent = store.get_relevant_memory("user_1", recent_k=5)
"""

from __future__ import annotations
import os
from typing import List, Optional, Callable, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, JSON, Index,
    func, select, and_, or_, desc, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# DB URL env var
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    # default to a local sqlite DB in project data dir for dev
    "sqlite:///./src/backend/data/memory.db"
)

# SQLAlchemy setup (sync). If you want async later, convert to async engine/async session.
ENGINE = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

Base = declarative_base()

def _now_utc():
    return datetime.now(timezone.utc)

class MemoryActive(Base):
    __tablename__ = "memory_active"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=_now_utc)
    role = Column(String, nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)

    # Simple text-search helper (SQLite fallback; for Postgres use full text or pg_trgm)
    __table_args__ = (
        Index("ix_memory_active_user_time", "user_id", "timestamp"),
    )

class MemoryArchive(Base):
    __tablename__ = "memory_archive"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_memory_archive_user_time", "user_id", "timestamp"),
    )

# Create tables (dev-time / startup)
def init_db():
    Base.metadata.create_all(bind=ENGINE)

# Type for tagger: callable(user_id, role, content) -> List[str]
TaggerFn = Callable[[str, str, str], List[str]]

class MemoryStore:
    def __init__(self,
                 db_session_factory: sessionmaker = SessionLocal,
                 max_active_per_user: int = 500,
                 archive_batch_size: int = 100,
                 taggers: Optional[List[TaggerFn]] = None):
        """
        :param db_session_factory: SQLAlchemy session factory
        :param max_active_per_user: keep this many most recent entries per user in active table
        :param archive_batch_size: how many entries to move at once when archiving
        :param taggers: list of callables that each return tags for a memory entry
        """
        self.db_session_factory = db_session_factory
        self.max_active_per_user = int(max_active_per_user)
        self.archive_batch_size = int(archive_batch_size)
        self.taggers = taggers or []

        # ensure DB/tables exist
        init_db()

    # --- low-level DB helpers ---
    def _get_session(self) -> Session:
        return self.db_session_factory()

    # --- core API ---
    def add_memory(self, user_id: str, role: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Add a memory entry. Returns the created entry dict.
        This will automatically call taggers and will enforce max_active_per_user by archiving oldest items.
        """
        session = self._get_session()
        try:
            # compute tags from injected taggers
            tags = tags or []
            for t in self.taggers:
                try:
                    t_tags = t(user_id, role, content)
                    if t_tags:
                        tags.extend(t_tags)
                except Exception:
                    # do not break on tagger failure
                    continue
            # normalize tags (unique)
            tags = list(dict.fromkeys(tags))

            entry = MemoryActive(
                id=str(uuid.uuid4()),
                user_id=user_id,
                timestamp=_now_utc(),
                role=role,
                content=content,
                tags=tags or None
            )
            session.add(entry)
            session.commit()

            # enforce active limit per user
            self._enforce_max_active_for_user(session, user_id)

            return self._to_dict(entry)
        finally:
            session.close()

    def _enforce_max_active_for_user(self, session: Session, user_id: str):
        """
        If active entries for a user exceed max_active_per_user, move the oldest entries to archive.
        This function moves entries in batches of archive_batch_size.
        """
        # count
        count_q = session.query(func.count(MemoryActive.id)).filter(MemoryActive.user_id == user_id)
        total = count_q.scalar() or 0
        if total <= self.max_active_per_user:
            return

        n_to_move = total - self.max_active_per_user
        # move in batches
        while n_to_move > 0:
            batch_size = min(self.archive_batch_size, n_to_move)
            # select oldest batch
            oldest = session.query(MemoryActive).filter(MemoryActive.user_id == user_id).order_by(MemoryActive.timestamp.asc()).limit(batch_size).all()
            if not oldest:
                break
            # move to archive
            for item in oldest:
                archive_item = MemoryArchive(
                    id=item.id,
                    user_id=item.user_id,
                    timestamp=item.timestamp,
                    role=item.role,
                    content=item.content,
                    tags=item.tags
                )
                session.add(archive_item)
                session.delete(item)
            session.commit()
            n_to_move -= len(oldest)

    def get_memory(self, user_id: str, limit: Optional[int] = None, include_archive: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve memory entries for the user, sorted newest-first.
        If include_archive=True, archived entries are included (they are appended after active entries).
        """
        session = self._get_session()
        try:
            q = session.query(MemoryActive).filter(MemoryActive.user_id == user_id).order_by(MemoryActive.timestamp.desc())
            active = q.limit(limit).all() if limit else q.all()
            results = [self._to_dict(o) for o in active]

            if include_archive:
                # append archived entries sorted desc
                aq = session.query(MemoryArchive).filter(MemoryArchive.user_id == user_id).order_by(MemoryArchive.timestamp.desc())
                archive = aq.limit(limit).all() if limit else aq.all()
                results.extend([self._to_dict(o) for o in archive])
            return results
        finally:
            session.close()

    def get_relevant_memory(self, user_id: str, recent_k: int = 5) -> List[Dict[str, Any]]:
        """
        Return the most recent recent_k entries from the active table for the user.
        """
        session = self._get_session()
        try:
            q = session.query(MemoryActive).filter(MemoryActive.user_id == user_id).order_by(MemoryActive.timestamp.desc()).limit(int(recent_k))
            rows = q.all()
            return [self._to_dict(r) for r in rows]
        finally:
            session.close()

    def search_memory(self, user_id: str, query: str, include_archive: bool = False, limit: Optional[int] = 50) -> List[Dict[str, Any]]:
        """
        Keyword substring search across content and tags. Case-insensitive.
        NOTE: This is a simple approach; for production semantic search use embeddings.
        """
        session = self._get_session()
        q_text = f"%{query.lower()}%"
        try:
            # search active
            active_q = session.query(MemoryActive).filter(
                and_(
                    MemoryActive.user_id == user_id,
                    or_(
                        func.lower(MemoryActive.content).like(q_text),
                        func.lower(func.coalesce(func.json_each_text(MemoryActive.tags), '')) .like(q_text)  # sqlite-friendly; not perfect
                    )
                )
            ).order_by(MemoryActive.timestamp.desc())
            active = active_q.limit(limit).all() if limit else active_q.all()
            results = [self._to_dict(a) for a in active]

            if include_archive:
                archive_q = session.query(MemoryArchive).filter(
                    and_(
                        MemoryArchive.user_id == user_id,
                        or_(
                            func.lower(MemoryArchive.content).like(q_text),
                            func.lower(func.coalesce(func.json_each_text(MemoryArchive.tags), '')).like(q_text)
                        )
                    )
                ).order_by(MemoryArchive.timestamp.desc())
                arch = archive_q.limit(limit).all() if limit else archive_q.all()
                results.extend([self._to_dict(a) for a in arch])

            return results[:limit] if limit else results
        finally:
            session.close()

    def export_memory(self, user_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export memory (active + archive) optionally for a single user.
        """
        session = self._get_session()
        try:
            if user_id:
                a = session.query(MemoryActive).filter(MemoryActive.user_id == user_id).order_by(MemoryActive.timestamp.asc()).all()
                ar = session.query(MemoryArchive).filter(MemoryArchive.user_id == user_id).order_by(MemoryArchive.timestamp.asc()).all()
            else:
                a = session.query(MemoryActive).order_by(MemoryActive.timestamp.asc()).all()
                ar = session.query(MemoryArchive).order_by(MemoryArchive.timestamp.asc()).all()
            return {
                "active": [self._to_dict(x) for x in a],
                "archive": [self._to_dict(x) for x in ar],
            }
        finally:
            session.close()

    def import_memory(self, payload: Dict[str, Any], merge: bool = True) -> None:
        """
        Import memory payload = {"active":[...], "archive":[...]}.
        If merge=False, clear existing tables and replace.
        """
        session = self._get_session()
        try:
            if not merge:
                session.query(MemoryActive).delete()
                session.query(MemoryArchive).delete()
                session.commit()

            for e in payload.get("active", []):
                item = MemoryActive(
                    id=e.get("id") or str(uuid.uuid4()),
                    user_id=e["user_id"],
                    timestamp=e.get("timestamp") or _now_utc(),
                    role=e.get("role") or "user",
                    content=e.get("content") or "",
                    tags=e.get("tags")
                )
                session.merge(item)
            for e in payload.get("archive", []):
                item = MemoryArchive(
                    id=e.get("id") or str(uuid.uuid4()),
                    user_id=e["user_id"],
                    timestamp=e.get("timestamp") or _now_utc(),
                    role=e.get("role") or "user",
                    content=e.get("content") or "",
                    tags=e.get("tags")
                )
                session.merge(item)
            session.commit()
        finally:
            session.close()

    # --- utilities ---
    def info(self) -> Dict[str, int]:
        session = self._get_session()
        try:
            active_total = session.query(func.count(MemoryActive.id)).scalar() or 0
            archive_total = session.query(func.count(MemoryArchive.id)).scalar() or 0
            active_users = session.query(func.count(func.distinct(MemoryActive.user_id))).scalar() or 0
            archive_users = session.query(func.count(func.distinct(MemoryArchive.user_id))).scalar() or 0
            return {
                "active_total": active_total,
                "archive_total": archive_total,
                "active_users": active_users,
                "archive_users": archive_users,
            }
        finally:
            session.close()

    def _to_dict(self, row) -> Dict[str, Any]:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "role": row.role,
            "content": row.content,
            "tags": row.tags or []
        }

# Helper to get a MemoryStore pre-wired with your taggers (if available)
def create_prod_memory_store(max_active_per_user: int = 500, archive_batch_size: int = 100, taggers: Optional[List[TaggerFn]] = None) -> MemoryStore:
    return MemoryStore(db_session_factory=SessionLocal, max_active_per_user=max_active_per_user, archive_batch_size=archive_batch_size, taggers=taggers or [])
