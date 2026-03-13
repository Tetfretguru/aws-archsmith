#!/usr/bin/env python3
"""Pydantic schemas for Archsmith API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StartRequest(BaseModel):
    session_id: str | None = None
    icon_set: str = Field(default="aws4", pattern="^(aws4|none)$")


class StartResponse(BaseModel):
    session_id: str
    icon_set: str
    ready: bool
    checks: list[str]
    active_file: str | None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    file_name: str | None = None
    icon_set: str | None = Field(default=None, pattern="^(aws4|none)$")


class ValidationStatus(BaseModel):
    ok: bool
    message: str


class ChatResponse(BaseModel):
    session_id: str
    changed: list[str]
    xml_path: str
    xml_content: str
    validation: ValidationStatus


class ValidateRequest(BaseModel):
    file_path: str | None = None
    xml_content: str | None = None


class ValidateResponse(BaseModel):
    validation: ValidationStatus
    xml_path: str | None = None


class FileResponse(BaseModel):
    xml_path: str
    xml_content: str
    validation: ValidationStatus


class SessionResponse(BaseModel):
    session_id: str
    icon_set: str
    active_file: str | None
    created_at: str
    updated_at: str
    counters: dict[str, int]
