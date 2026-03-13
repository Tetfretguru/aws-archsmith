#!/usr/bin/env python3
"""Diagram operations for interactive Archsmith CLI."""

from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from generate_xml import (
    SERVICE_MAP,
    add_cell,
    add_edge,
    build_diagram,
    indent,
    parse_services,
    service_group,
    service_style,
    slugify,
)
from validate_drawio import validate_file


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "architecture" / "raw"
RENDERED_DIR = ROOT / "architecture" / "rendered"
TMP_RENDER_INPUT = ROOT / "architecture" / "specs" / "cli-render-input"

BOUNDARY_IDS = {
    "vpc",
    "public-subnet",
    "private-subnet",
    "account-eop",
    "account-pdv",
    "account-datalake",
}
BOUNDARY_VALUES = {"VPC", "Public Subnet", "Private Subnet"}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "architecture" / "specs").mkdir(parents=True, exist_ok=True)
    TMP_RENDER_INPUT.mkdir(parents=True, exist_ok=True)


def startup_check() -> tuple[bool, list[str]]:
    lines: list[str] = []
    ok = True

    py = shutil.which("python3")
    if py:
        lines.append(f"[ok] python3: {py}")
    else:
        lines.append("[error] python3 not found in PATH")
        ok = False

    docker = shutil.which("docker")
    if docker:
        lines.append(f"[ok] docker: {docker}")
    else:
        lines.append("[error] docker not found in PATH")
        ok = False

    if docker:
        proc = subprocess.run(["docker", "compose", "version"], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode == 0:
            first = (proc.stdout.strip() or proc.stderr.strip()).splitlines()[0]
            lines.append(f"[ok] docker compose: {first}")
        else:
            lines.append("[error] docker compose is not available")
            ok = False

    try:
        ensure_dirs()
        lines.append("[ok] workspace dirs: architecture/raw architecture/rendered architecture/specs")
    except Exception as exc:
        lines.append(f"[error] workspace setup failed: {exc}")
        ok = False

    return ok, lines


def now_name(prefix: str = "session") -> str:
    return f"{prefix}-{dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"


def _graph_root(tree: object) -> ET.Element:
    if not hasattr(tree, "getroot"):
        raise RuntimeError("Invalid drawio structure: tree has no getroot")
    root = tree.getroot()  # type: ignore[attr-defined]
    if root is None:
        raise RuntimeError("Invalid drawio structure: empty XML root")
    graph_root = root.find("./diagram/mxGraphModel/root")
    if graph_root is None:
        raise RuntimeError("Invalid drawio structure: missing diagram/mxGraphModel/root")
    return graph_root


def _service_cells(graph_root: ET.Element) -> list[ET.Element]:
    out: list[ET.Element] = []
    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        cid = cell.get("id", "")
        value = cell.get("value", "")
        if cid in BOUNDARY_IDS or value in BOUNDARY_VALUES or value.startswith("AWS Account"):
            continue
        out.append(cell)
    return out


def _cell_geometry(cell: ET.Element) -> tuple[float, float, float, float]:
    geom = cell.find("mxGeometry")
    if geom is None:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        float(geom.get("x", "0")),
        float(geom.get("y", "0")),
        float(geom.get("width", "0")),
        float(geom.get("height", "0")),
    )


def _service_map_by_value(graph_root: ET.Element) -> dict[str, ET.Element]:
    out: dict[str, ET.Element] = {}
    for cell in _service_cells(graph_root):
        value = cell.get("value", "").strip()
        if value:
            out[value.lower()] = cell
    return out


def _canonical_from_text(text: str) -> list[str]:
    p = text.lower()
    found: list[str] = []
    for key, label in SERVICE_MAP.items():
        if key in p and label not in found:
            found.append(label)
    return found


def generate_new(name: str, prompt: str, icon_set: str = "aws4") -> Path:
    ensure_dirs()
    tree = build_diagram(name, prompt, icon_set, box_fill="auto")
    out = RAW_DIR / f"{slugify(name)}.drawio"
    root = tree.getroot()
    if root is None:
        raise RuntimeError("Failed to build XML root element")
    indent(root)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def validate_path(path: Path) -> tuple[bool, str]:
    errors = validate_file(path)
    if errors:
        return False, "\n".join(errors)
    return True, f"Validation passed for {path.name}"


def render_file(path: Path) -> tuple[bool, str, Path | None]:
    ensure_dirs()
    for file in TMP_RENDER_INPUT.glob("*.drawio"):
        file.unlink()
    tmp_file = TMP_RENDER_INPUT / path.name
    shutil.copy2(path, tmp_file)

    cmd = [
        "docker",
        "compose",
        "-f",
        "docker/compose.yml",
        "run",
        "--rm",
        "renderer",
        "architecture/specs/cli-render-input",
        "architecture/rendered",
        "png",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    png = RENDERED_DIR / f"{path.stem}.png"
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "Render failed"
        return False, detail, None
    if not png.exists():
        return False, "Render command finished but PNG was not found", None
    return True, f"Rendered {png.name}", png


def summarize(path: Path) -> str:
    tree = ET.parse(path)
    graph_root = _graph_root(tree)
    services = [c.get("value", "") for c in _service_cells(graph_root)]
    edges = [c for c in graph_root.findall("mxCell") if c.get("edge") == "1"]
    return f"services={len(services)}, edges={len(edges)}, file={path.name}"


def _next_edge_id(graph_root: ET.Element) -> str:
    max_n = 0
    for cell in graph_root.findall("mxCell"):
        cid = cell.get("id", "")
        if cid.startswith("e-"):
            try:
                max_n = max(max_n, int(cid.split("-", 1)[1]))
            except ValueError:
                continue
    return f"e-{max_n + 1}"


def _add_service(graph_root: ET.Element, service: str, icon_set: str) -> bool:
    existing = _service_map_by_value(graph_root)
    if service.lower() in existing:
        return False

    group = service_group(service)
    parent = "private-subnet" if graph_root.find("mxCell[@id='private-subnet']") is not None else "1"
    if group in {"ingress", "security", "observability"}:
        parent = "1"
    elif group == "network" and graph_root.find("mxCell[@id='public-subnet']") is not None:
        parent = "public-subnet"

    sibling_cells = [c for c in _service_cells(graph_root) if c.get("parent", "1") == parent and service_group(c.get("value", "")) == group]
    row = len(sibling_cells)

    if group == "ingress":
        x, y, step = 30, 60, 118
    elif group == "security":
        x, y, step = 300, 20, 108
    elif group == "observability":
        x, y, step = 1160, 20, 108
    elif group == "network":
        x, y, step = 70, 120, 108
    elif group == "messaging":
        x, y, step = 30, 330, 108
    elif group == "data":
        x, y, step = 260, 60, 112
    else:
        x, y, step = 30, 60, 112

    add_cell(
        graph_root,
        cell_id=slugify(service),
        value=service,
        style=service_style(service, icon_set, filled=False),
        x=x,
        y=y + row * step,
        w=96 if icon_set == "aws4" else 220,
        h=96 if icon_set == "aws4" else 60,
        parent=parent,
    )
    return True


def _remove_service(graph_root: ET.Element, service: str) -> bool:
    target = None
    target_id = ""
    for cell in _service_cells(graph_root):
        if cell.get("value", "").lower() == service.lower():
            target = cell
            target_id = cell.get("id", "")
            break
    if target is None:
        return False

    graph_root.remove(target)
    for edge in list(graph_root.findall("mxCell")):
        if edge.get("edge") != "1":
            continue
        if edge.get("source") == target_id or edge.get("target") == target_id:
            graph_root.remove(edge)
    return True


def _resolve_service_id(graph_root: ET.Element, text: str) -> str | None:
    key = text.strip().lower()
    aliases = _canonical_from_text(text)

    for cell in _service_cells(graph_root):
        value = cell.get("value", "").strip()
        if value.lower() == key:
            return cell.get("id")

    if aliases:
        wanted = aliases[0].lower()
        for cell in _service_cells(graph_root):
            value = cell.get("value", "").strip().lower()
            if value == wanted:
                return cell.get("id")

    for cell in _service_cells(graph_root):
        value = cell.get("value", "").strip().lower()
        if key and key in value:
            return cell.get("id")
    return None


def _connect_services(graph_root: ET.Element, source_text: str, target_text: str, label: str = "") -> bool:
    source_id = _resolve_service_id(graph_root, source_text)
    target_id = _resolve_service_id(graph_root, target_text)
    if not source_id or not target_id:
        return False

    for edge in graph_root.findall("mxCell"):
        if edge.get("edge") == "1" and edge.get("source") == source_id and edge.get("target") == target_id:
            return False

    by_id = {c.get("id", ""): c for c in _service_cells(graph_root)}
    source_box = _cell_geometry(by_id[source_id]) if source_id in by_id else None
    target_box = _cell_geometry(by_id[target_id]) if target_id in by_id else None
    add_edge(
        graph_root,
        edge_id=_next_edge_id(graph_root),
        source=source_id,
        target=target_id,
        source_box=source_box,
        target_box=target_box,
        label=label,
    )
    return True


def apply_prompt_delta(path: Path, prompt: str, icon_set: str = "aws4") -> list[str]:
    tree = ET.parse(path)
    graph_root = _graph_root(tree)
    changes: list[str] = []
    p = prompt.lower()

    remove_mode = any(word in p for word in ["remove", "delete", "drop"])
    connect_mode = "->" in prompt or "connect" in p

    services = parse_services(prompt)
    if remove_mode:
        for svc in services:
            if _remove_service(graph_root, svc):
                changes.append(f"removed {svc}")
    else:
        for svc in services:
            if _add_service(graph_root, svc, icon_set):
                changes.append(f"added {svc}")

    def _clean_token(token: str) -> str:
        token = token.strip()
        token = re.sub(r"^(connect|from|to)\s+", "", token, flags=re.IGNORECASE)
        token = re.sub(r"\s+(to|from)$", "", token, flags=re.IGNORECASE)
        return token.strip(" ,.;:")

    arrow_pairs: list[tuple[str, str]] = []
    if "->" in prompt:
        parts = [_clean_token(x) for x in prompt.split("->")]
        parts = [x for x in parts if x]
        for i in range(len(parts) - 1):
            arrow_pairs.append((parts[i], parts[i + 1]))

    for left, right in arrow_pairs:
        label = ""
        if "post" in p:
            label = "POST"
        elif "daily" in p or "schedule" in p:
            label = "DAILY"
        elif "unload" in p:
            label = "UNLOAD"
        elif "stream" in p:
            label = "STREAM"
        if _connect_services(graph_root, left, right, label=label):
            changes.append(f"connected {left.strip()} -> {right.strip()}")

    if connect_mode and not arrow_pairs and len(services) >= 2:
        if _connect_services(graph_root, services[0], services[1]):
            changes.append(f"connected {services[0]} -> {services[1]}")

    root = tree.getroot()
    root.set("modified", dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    indent(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return changes or ["no structural changes detected"]
