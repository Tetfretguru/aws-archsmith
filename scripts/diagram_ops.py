#!/usr/bin/env python3
"""Diagram operations for interactive Archsmith CLI."""

from __future__ import annotations

import datetime as dt
import base64
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from urllib.parse import unquote

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

DEFAULT_BOUNDARY_IDS = {
    "vpc",
    "public-subnet",
    "private-subnet",
}
DEFAULT_BOUNDARY_VALUES = {"VPC", "Public Subnet", "Private Subnet"}
BOUNDARY_STYLE_TOKENS = (
    "swimlane",
    "container=1",
    "dashed=1",
)
KNOWN_SERVICES = set(SERVICE_MAP.values())


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "architecture" / "specs").mkdir(parents=True, exist_ok=True)
    TMP_RENDER_INPUT.mkdir(parents=True, exist_ok=True)


def startup_check(*, require_docker: bool = True) -> tuple[bool, list[str]]:
    lines: list[str] = []
    ok = True

    py = shutil.which("python3")
    if py:
        lines.append(f"[ok] python3: {py}")
    else:
        lines.append("[error] python3 not found in PATH")
        ok = False

    docker = shutil.which("docker")
    if require_docker:
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
    else:
        lines.append("[ok] docker check skipped (API XML-only mode)")

    try:
        ensure_dirs()
        lines.append("[ok] workspace dirs: architecture/raw architecture/rendered architecture/specs")
    except Exception as exc:
        lines.append(f"[error] workspace setup failed: {exc}")
        ok = False

    return ok, lines


def now_name(prefix: str = "session") -> str:
    return f"{prefix}-{dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"


def _decode_compressed_diagram_xml(encoded_payload: str) -> ET.Element:
    try:
        compressed = base64.b64decode(encoded_payload)
        inflated = zlib.decompress(compressed, -15)
        decoded = unquote(inflated.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Invalid drawio compressed diagram payload") from exc

    try:
        return ET.fromstring(decoded)
    except ET.ParseError as exc:
        raise RuntimeError("Decoded drawio diagram is not valid XML") from exc


def _load_tree_and_graph(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    if root is None:
        raise RuntimeError("Invalid drawio structure: empty XML root")

    direct_graph_root = root.find("./diagram/mxGraphModel/root")
    if direct_graph_root is not None:
        return tree, direct_graph_root, False

    diagram = root.find("diagram")
    if diagram is None:
        raise RuntimeError("Invalid drawio structure: missing diagram element")

    payload = (diagram.text or "").strip()
    if not payload:
        raise RuntimeError("Invalid drawio structure: missing diagram/mxGraphModel/root")

    decoded_model = _decode_compressed_diagram_xml(payload)
    diagram_attrs = dict(diagram.attrib)
    diagram.clear()
    diagram.attrib.update(diagram_attrs)
    diagram.text = None
    diagram.append(decoded_model)

    graph_root = root.find("./diagram/mxGraphModel/root")
    if graph_root is None:
        raise RuntimeError("Invalid drawio structure: missing diagram/mxGraphModel/root")
    return tree, graph_root, True


def _clone_element(element: ET.Element) -> ET.Element:
    return ET.fromstring(ET.tostring(element, encoding="utf-8"))


def _boundary_parent_ids(graph_root: ET.Element) -> set[str]:
    out: set[str] = set()
    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        parent = cell.get("parent", "")
        if parent and parent not in {"0", "1"}:
            out.add(parent)
    return out


def _looks_like_boundary(cell: ET.Element, parent_ids: set[str]) -> bool:
    cid = cell.get("id", "")
    value = cell.get("value", "").strip()
    style = cell.get("style", "").lower()
    x, y, w, h = _cell_geometry(cell)

    if cid in DEFAULT_BOUNDARY_IDS or value in DEFAULT_BOUNDARY_VALUES:
        return True
    if value.startswith("AWS Account"):
        return True
    if any(token in style for token in BOUNDARY_STYLE_TOKENS):
        return True
    if cid in parent_ids and w >= 260 and h >= 160:
        return True
    if value and any(word in value.lower() for word in ["account", "subnet", "vpc", "boundary"]) and w >= 200 and h >= 120:
        return True
    if w >= 700 and h >= 450 and (x >= 0 or y >= 0):
        return True
    return False


def _boundary_cells(graph_root: ET.Element) -> list[ET.Element]:
    parent_ids = _boundary_parent_ids(graph_root)
    out: list[ET.Element] = []
    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        if _looks_like_boundary(cell, parent_ids):
            out.append(cell)
    return out


def _boundary_ids(graph_root: ET.Element) -> set[str]:
    return {cell.get("id", "") for cell in _boundary_cells(graph_root) if cell.get("id")}


def _boundary_id_by_keyword(graph_root: ET.Element, keywords: tuple[str, ...]) -> str | None:
    for cell in _boundary_cells(graph_root):
        label = cell.get("value", "").strip().lower()
        if not label:
            continue
        if any(key in label for key in keywords):
            cid = cell.get("id")
            if cid:
                return cid
    return None


def _largest_boundary_id(graph_root: ET.Element) -> str | None:
    largest_id: str | None = None
    largest_area = -1.0
    for cell in _boundary_cells(graph_root):
        cid = cell.get("id")
        if not cid:
            continue
        _, _, w, h = _cell_geometry(cell)
        area = w * h
        if area > largest_area:
            largest_area = area
            largest_id = cid
    return largest_id


def _default_parent_for_group(graph_root: ET.Element, group: str) -> str:
    if group in {"ingress", "security", "observability"}:
        return "1"

    private_id = _boundary_id_by_keyword(graph_root, ("private",))
    public_id = _boundary_id_by_keyword(graph_root, ("public",))

    if group == "network" and public_id:
        return public_id
    if private_id:
        return private_id

    account_id = _boundary_id_by_keyword(graph_root, ("account", "workload", "application", "app"))
    if account_id:
        return account_id

    largest = _largest_boundary_id(graph_root)
    if largest and largest != "1":
        return largest
    return "1"


def _service_cells(graph_root: ET.Element) -> list[ET.Element]:
    out: list[ET.Element] = []
    boundary_ids = _boundary_ids(graph_root)
    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        cid = cell.get("id", "")
        if cid in boundary_ids:
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
    _, graph_root, was_compressed = _load_tree_and_graph(path)
    services = [c.get("value", "") for c in _service_cells(graph_root)]
    edges = [c for c in graph_root.findall("mxCell") if c.get("edge") == "1"]
    fmt = "compressed" if was_compressed else "uncompressed"
    return f"services={len(services)}, edges={len(edges)}, format={fmt}, file={path.name}"


def understand_diagram(path: Path) -> dict[str, object]:
    _, graph_root, was_compressed = _load_tree_and_graph(path)

    cells = graph_root.findall("mxCell")
    by_id = {cell.get("id", ""): cell for cell in cells}
    services = _service_cells(graph_root)

    recognized: list[str] = []
    unknown: list[str] = []
    for cell in services:
        value = cell.get("value", "").strip()
        if not value:
            continue
        if value in KNOWN_SERVICES:
            recognized.append(value)
        else:
            unknown.append(value)

    edges: list[str] = []
    for edge in cells:
        if edge.get("edge") != "1":
            continue
        source_id = edge.get("source", "")
        target_id = edge.get("target", "")
        source_raw = by_id.get(source_id, edge).get("value", source_id)
        target_raw = by_id.get(target_id, edge).get("value", target_id)
        source_label = str(source_raw or source_id).strip() or source_id
        target_label = str(target_raw or target_id).strip() or target_id
        label = (edge.get("value", "") or "").strip()
        if label:
            edges.append(f"{source_label} -> {target_label} [{label}]")
        else:
            edges.append(f"{source_label} -> {target_label}")

    boundaries = [cell.get("value", cell.get("id", "")) for cell in _boundary_cells(graph_root)]

    return {
        "file": str(path),
        "format": "compressed" if was_compressed else "uncompressed",
        "services_count": len(services),
        "edges_count": len(edges),
        "recognized_services": sorted(set(recognized)),
        "unknown_components": sorted(set(unknown)),
        "boundaries": boundaries,
        "inferred_flows": edges,
    }


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
    parent = _default_parent_for_group(graph_root, group)

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
        w=78 if icon_set == "aws4" else 220,
        h=78 if icon_set == "aws4" else 60,
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


def _clean_token(token: str) -> str:
    token = token.strip()
    token = re.sub(r"^(connect|from|to)\s+", "", token, flags=re.IGNORECASE)
    token = re.sub(r"\s+(to|from)$", "", token, flags=re.IGNORECASE)
    return token.strip(" ,.;:")


def _arrow_pairs(prompt: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if "->" not in prompt:
        return out
    parts = [_clean_token(x) for x in prompt.split("->")]
    parts = [x for x in parts if x]
    for i in range(len(parts) - 1):
        out.append((parts[i], parts[i + 1]))
    return out


def _edge_label(prompt: str) -> str:
    p = prompt.lower()
    if "post" in p:
        return "POST"
    if "daily" in p or "schedule" in p:
        return "DAILY"
    if "unload" in p:
        return "UNLOAD"
    if "stream" in p:
        return "STREAM"
    return ""


def _collect_prompt_changes(graph_root: ET.Element, prompt: str, icon_set: str) -> list[str]:
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

    arrow_pairs = _arrow_pairs(prompt)
    label = _edge_label(prompt)
    for left, right in arrow_pairs:
        if _connect_services(graph_root, left, right, label=label):
            changes.append(f"connected {left.strip()} -> {right.strip()}")

    if connect_mode and not arrow_pairs and len(services) >= 2:
        if _connect_services(graph_root, services[0], services[1], label=label):
            changes.append(f"connected {services[0]} -> {services[1]}")

    return changes


def plan_prompt_delta(path: Path, prompt: str, icon_set: str = "aws4") -> list[str]:
    _, graph_root, _ = _load_tree_and_graph(path)
    simulated_graph = _clone_element(graph_root)
    changes = _collect_prompt_changes(simulated_graph, prompt, icon_set)
    return [f"would {change}" for change in changes] or ["no structural changes detected"]


def apply_prompt_delta(path: Path, prompt: str, icon_set: str = "aws4") -> list[str]:
    tree, graph_root, _ = _load_tree_and_graph(path)
    changes = _collect_prompt_changes(graph_root, prompt, icon_set)

    root = tree.getroot()
    root.set("modified", dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    indent(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return changes or ["no structural changes detected"]
