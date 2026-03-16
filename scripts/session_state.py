#!/usr/bin/env python3
"""Interactive session state for Archsmith CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionState:
    active_file: Path | None = None
    icon_set: str = "aws4"
    last_validation_ok: bool | None = None
    last_validation_msg: str = ""
    last_rendered_png: Path | None = None
    pending_redefine_prompt: str | None = None
    pending_redefine_plan: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
