#!/usr/bin/env python3
"""Database layer for Archsmith API."""

from __future__ import annotations

import datetime as dt
import os
import uuid
from pathlib import Path

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, func, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE = f"sqlite:///{ROOT / 'architecture' / 'specs' / 'api' / 'archsmith.db'}"


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    active_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    icon_set: Mapped[str] = mapped_column(String(32), default="aws4")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    messages: Mapped[list[Message]] = relationship(back_populates="session")
    operations: Mapped[list[Operation]] = relationship(back_populates="session")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="session")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="operations")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    xml_content: Mapped[str] = mapped_column(Text)
    validation_ok: Mapped[bool] = mapped_column(Boolean)
    validation_message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="artifacts")


DB_URL = os.getenv("ARCHSMITH_DB_URL", DEFAULT_SQLITE)
if DB_URL.startswith("sqlite:///"):
    sqlite_path = Path(DB_URL.replace("sqlite:///", "", 1))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def db_healthcheck() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "database reachable"
    except Exception as exc:
        return False, str(exc)


def get_or_create_session(db: Session, session_id: str | None = None, icon_set: str = "aws4") -> ChatSession:
    if session_id:
        existing = db.get(ChatSession, session_id)
        if existing is not None:
            return existing

    sid = session_id or str(uuid.uuid4())
    sess = ChatSession(id=sid, icon_set=icon_set, created_at=dt.datetime.utcnow(), updated_at=dt.datetime.utcnow())
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def touch_session(db: Session, session: ChatSession, *, active_file: str | None = None, icon_set: str | None = None) -> None:
    if active_file is not None:
        session.active_file = active_file
    if icon_set is not None:
        session.icon_set = icon_set
    session.updated_at = dt.datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)


def add_message(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(Message(session_id=session_id, role=role, content=content, created_at=dt.datetime.utcnow()))
    db.commit()


def add_operation(db: Session, session_id: str, kind: str, status: str, detail: str) -> None:
    db.add(
        Operation(
            session_id=session_id,
            kind=kind,
            status=status,
            detail=detail,
            created_at=dt.datetime.utcnow(),
        )
    )
    db.commit()


def add_artifact(db: Session, session_id: str, file_path: str, xml_content: str, validation_ok: bool, validation_message: str) -> None:
    db.add(
        Artifact(
            session_id=session_id,
            file_path=file_path,
            xml_content=xml_content,
            validation_ok=validation_ok,
            validation_message=validation_message,
            created_at=dt.datetime.utcnow(),
        )
    )
    db.commit()


def session_summary(db: Session, session_id: str) -> dict[str, int]:
    message_count = db.scalar(select(func.count(Message.id)).where(Message.session_id == session_id))
    operation_count = db.scalar(select(func.count(Operation.id)).where(Operation.session_id == session_id))
    artifact_count = db.scalar(select(func.count(Artifact.id)).where(Artifact.session_id == session_id))
    return {
        "messages": int(message_count or 0),
        "operations": int(operation_count or 0),
        "artifacts": int(artifact_count or 0),
    }
