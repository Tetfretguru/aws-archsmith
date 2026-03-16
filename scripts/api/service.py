#!/usr/bin/env python3
"""Business logic for Archsmith API."""

from __future__ import annotations

import tempfile
from pathlib import Path

from diagram_ops import (
    RAW_DIR,
    apply_prompt_delta,
    ensure_dirs,
    generate_new,
    now_name,
    plan_prompt_delta,
    startup_check,
    understand_diagram,
    validate_path,
)
from generate_xml import parse_services, slugify


def run_startup() -> tuple[bool, list[str]]:
    return startup_check(require_docker=False)


def resolve_raw_file(file_name: str) -> Path:
    p = Path(file_name)
    if p.suffix != ".drawio":
        p = p.with_suffix(".drawio")
    if p.is_absolute():
        return p
    return RAW_DIR / p.name


def chat_apply(*, message: str, active_file: Path | None, file_name: str | None, icon_set: str) -> tuple[Path, list[str]]:
    ensure_dirs()

    if active_file is None and file_name:
        active_file = resolve_raw_file(file_name)

    if active_file is None or not active_file.exists():
        base_name = slugify(file_name) if file_name else now_name("api")
        out = generate_new(name=base_name, prompt=message, icon_set=icon_set)
        return out, [f"generated {out.name}"]

    changes = apply_prompt_delta(active_file, message, icon_set=icon_set)
    return active_file, changes


def validate_inline_xml(xml_content: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", encoding="utf-8", delete=False) as tmp:
        tmp.write(xml_content)
        tmp_path = Path(tmp.name)

    ok, msg = validate_path(tmp_path)
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass
    return ok, msg


def read_xml(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_existing_file(*, session_active_file: str | None, file_path: str | None) -> Path:
    candidate = resolve_raw_file(file_path) if file_path else (Path(session_active_file) if session_active_file else None)
    if candidate is None:
        raise FileNotFoundError("no active file; provide file_path or chat first")
    if not candidate.exists():
        raise FileNotFoundError(f"file not found: {candidate}")
    return candidate


def understand_existing(*, session_active_file: str | None, file_path: str | None) -> dict[str, object]:
    path = resolve_existing_file(session_active_file=session_active_file, file_path=file_path)
    return understand_diagram(path)


def _auto_name(file_name: str | None) -> str:
    if file_name:
        return slugify(file_name)
    return now_name("arch")


def plan_redefine(
    *,
    message: str,
    session_active_file: str | None,
    file_path: str | None,
    file_name: str | None,
    icon_set: str,
) -> tuple[Path, list[str], bool]:
    try:
        path = resolve_existing_file(session_active_file=session_active_file, file_path=file_path)
        changes = plan_prompt_delta(path, message, icon_set=icon_set)
        return path, changes, True
    except FileNotFoundError:
        ensure_dirs()
        draft_name = _auto_name(file_name)
        draft_path = resolve_raw_file(draft_name)
        services = parse_services(message)
        changes = [f"would create {draft_path.name}"]
        if services:
            changes.extend([f"would add {svc}" for svc in services])
        else:
            changes.append("would generate architecture from prompt")
        return draft_path, changes, False


def apply_redefine(
    *,
    message: str,
    session_active_file: str | None,
    file_path: str | None,
    file_name: str | None,
    icon_set: str,
) -> tuple[Path, list[str]]:
    try:
        path = resolve_existing_file(session_active_file=session_active_file, file_path=file_path)
        changes = apply_prompt_delta(path, message, icon_set=icon_set)
        return path, changes
    except FileNotFoundError:
        base_name = _auto_name(file_name)
        out = generate_new(name=base_name, prompt=message, icon_set=icon_set)
        return out, [f"generated {out.name}"]
