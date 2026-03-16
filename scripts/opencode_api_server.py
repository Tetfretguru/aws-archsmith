#!/usr/bin/env python3
"""Archsmith API server for natural-language XML operations."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from api.db import (
    ChatSession,
    SessionLocal,
    add_artifact,
    add_message,
    add_operation,
    db_healthcheck,
    get_or_create_session,
    init_db,
    session_summary,
    touch_session,
)
from api.schemas import (
    ChatRequest,
    ChatResponse,
    DiagramRedefineApplyRequest,
    DiagramRedefineApplyResponse,
    DiagramRedefinePlanRequest,
    DiagramRedefinePlanResponse,
    DiagramUnderstandRequest,
    DiagramUnderstandResponse,
    FileResponse,
    SessionResponse,
    StartRequest,
    StartResponse,
    ValidateRequest,
    ValidateResponse,
    ValidationStatus,
)
from api.service import (
    apply_redefine,
    chat_apply,
    plan_redefine,
    read_xml,
    resolve_raw_file,
    run_startup,
    understand_existing,
    validate_inline_xml,
)
from diagram_ops import validate_path


app = FastAPI(title="aws-archsmith API", version="0.1.0")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    ok, detail = db_healthcheck()
    if not ok:
        raise HTTPException(status_code=500, detail=f"database error: {detail}")
    return {"status": "ok", "database": detail}


@app.post("/v1/start", response_model=StartResponse)
def start(payload: StartRequest, db: Session = Depends(get_db)) -> StartResponse:
    ready, checks = run_startup()
    session = get_or_create_session(db, session_id=payload.session_id, icon_set=payload.icon_set)
    touch_session(db, session, icon_set=payload.icon_set)
    return StartResponse(
        session_id=session.id,
        icon_set=session.icon_set,
        ready=ready,
        checks=checks,
        active_file=session.active_file,
    )


@app.post("/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = get_or_create_session(db, session_id=payload.session_id)
    icon_set = payload.icon_set or session.icon_set

    active = Path(session.active_file) if session.active_file else None

    try:
        xml_path, changes = chat_apply(
            message=payload.message,
            active_file=active,
            file_name=payload.file_name,
            icon_set=icon_set,
        )
    except Exception as exc:
        add_operation(db, session.id, kind="chat", status="error", detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    ok, msg = validate_path(xml_path)
    xml_content = read_xml(xml_path)

    touch_session(db, session, active_file=str(xml_path), icon_set=icon_set)
    add_message(db, session.id, "user", payload.message)
    add_message(db, session.id, "assistant", "; ".join(changes))
    add_operation(db, session.id, kind="chat", status="success" if ok else "validation_failed", detail=msg)
    add_artifact(db, session.id, str(xml_path), xml_content, ok, msg)

    if not ok:
        raise HTTPException(
            status_code=422,
            detail={
                "session_id": session.id,
                "changed": changes,
                "xml_path": str(xml_path),
                "validation": msg,
            },
        )

    return ChatResponse(
        session_id=session.id,
        changed=changes,
        xml_path=str(xml_path),
        xml_content=xml_content,
        validation=ValidationStatus(ok=ok, message=msg),
    )


@app.post("/v1/validate", response_model=ValidateResponse)
def validate(payload: ValidateRequest) -> ValidateResponse:
    if payload.file_path:
        path = resolve_raw_file(payload.file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"file not found: {path}")
        ok, msg = validate_path(path)
        status = ValidationStatus(ok=ok, message=msg)
        return ValidateResponse(validation=status, xml_path=str(path))

    if payload.xml_content:
        ok, msg = validate_inline_xml(payload.xml_content)
        return ValidateResponse(validation=ValidationStatus(ok=ok, message=msg), xml_path=None)

    raise HTTPException(status_code=400, detail="provide file_path or xml_content")


@app.get("/v1/file", response_model=FileResponse)
def get_file(
    file_path: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> FileResponse:
    path: Path | None = None
    if file_path:
        path = resolve_raw_file(file_path)
    elif session_id:
        sess = db.get(ChatSession, session_id)
        if sess is None:
            raise HTTPException(status_code=404, detail=f"session not found: {session_id}")
        if not sess.active_file:
            raise HTTPException(status_code=404, detail="session has no active file")
        path = Path(sess.active_file)
    else:
        raise HTTPException(status_code=400, detail="provide file_path or session_id")

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {path}")

    xml_content = read_xml(path)
    ok, msg = validate_path(path)
    return FileResponse(
        xml_path=str(path),
        xml_content=xml_content,
        validation=ValidationStatus(ok=ok, message=msg),
    )


@app.get("/v1/session/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionResponse:
    sess = db.get(ChatSession, session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail=f"session not found: {session_id}")

    return SessionResponse(
        session_id=sess.id,
        icon_set=sess.icon_set,
        active_file=sess.active_file,
        created_at=sess.created_at.isoformat() + "Z",
        updated_at=sess.updated_at.isoformat() + "Z",
        counters=session_summary(db, session_id),
    )


@app.post("/v1/diagram/understand", response_model=DiagramUnderstandResponse)
def diagram_understand(payload: DiagramUnderstandRequest, db: Session = Depends(get_db)) -> DiagramUnderstandResponse:
    session_id = payload.session_id
    active_file = None
    if session_id:
        sess = db.get(ChatSession, session_id)
        if sess is None:
            raise HTTPException(status_code=404, detail=f"session not found: {session_id}")
        active_file = sess.active_file

    try:
        summary = understand_existing(session_active_file=active_file, file_path=payload.file_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DiagramUnderstandResponse(session_id=session_id, summary=summary)


@app.post("/v1/diagram/redefine/plan", response_model=DiagramRedefinePlanResponse)
def diagram_redefine_plan(payload: DiagramRedefinePlanRequest, db: Session = Depends(get_db)) -> DiagramRedefinePlanResponse:
    session = get_or_create_session(db, session_id=payload.session_id) if payload.session_id else None
    session_id = session.id if session else None
    icon_set = payload.icon_set or (session.icon_set if session else "aws4")
    active_file = session.active_file if session else None

    try:
        path, planned, materialized = plan_redefine(
            message=payload.message,
            session_active_file=active_file,
            file_path=payload.file_path,
            file_name=payload.file_name,
            icon_set=icon_set,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if materialized:
        ok, msg = validate_path(path)
    else:
        ok, msg = True, f"Plan generated for new file {path.name}; validation will run on apply"
    if session:
        touch_session(db, session, active_file=(str(path) if materialized else session.active_file), icon_set=icon_set)
        add_operation(db, session.id, kind="diagram_redefine_plan", status="success" if ok else "validation_failed", detail=msg)

    return DiagramRedefinePlanResponse(
        session_id=session_id,
        file_path=str(path),
        planned_changes=planned,
        validation=ValidationStatus(ok=ok, message=msg),
    )


@app.post("/v1/diagram/redefine/apply", response_model=DiagramRedefineApplyResponse)
def diagram_redefine_apply(payload: DiagramRedefineApplyRequest, db: Session = Depends(get_db)) -> DiagramRedefineApplyResponse:
    session = get_or_create_session(db, session_id=payload.session_id) if payload.session_id else None
    session_id = session.id if session else None
    icon_set = payload.icon_set or (session.icon_set if session else "aws4")
    active_file = session.active_file if session else None

    try:
        path, changed = apply_redefine(
            message=payload.message,
            session_active_file=active_file,
            file_path=payload.file_path,
            file_name=payload.file_name,
            icon_set=icon_set,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    xml_content = read_xml(path)
    ok, msg = validate_path(path)

    if session:
        touch_session(db, session, active_file=str(path), icon_set=icon_set)
        add_message(db, session.id, "user", payload.message)
        add_message(db, session.id, "assistant", "; ".join(changed))
        add_operation(db, session.id, kind="diagram_redefine_apply", status="success" if ok else "validation_failed", detail=msg)
        add_artifact(db, session.id, str(path), xml_content, ok, msg)

    return DiagramRedefineApplyResponse(
        session_id=session_id,
        file_path=str(path),
        changed=changed,
        xml_content=xml_content,
        validation=ValidationStatus(ok=ok, message=msg),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Archsmith API server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run("opencode_api_server:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
