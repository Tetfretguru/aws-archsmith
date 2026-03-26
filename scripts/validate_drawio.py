#!/usr/bin/env python3
"""Validate Draw.io XML structure and basic architecture constraints."""

from __future__ import annotations

import argparse
import pathlib
import sys
import xml.etree.ElementTree as ET


def has_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def validate_file(path: pathlib.Path) -> list[str]:
    errors: list[str] = []

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path}: XML parse error: {exc}"]

    root = tree.getroot()
    if root.tag != "mxfile":
        errors.append(f"{path}: root element must be <mxfile>")
        return errors

    model = root.find("./diagram/mxGraphModel")
    if model is None:
        errors.append(f"{path}: missing ./diagram/mxGraphModel")
        return errors

    graph_root = model.find("root")
    if graph_root is None:
        errors.append(f"{path}: missing mxGraphModel/root")
        return errors

    ids = {cell.get("id") for cell in graph_root.findall("mxCell")}
    if "0" not in ids or "1" not in ids:
        errors.append(f"{path}: required base mxCell ids 0 and 1 are missing")

    edge_ids = {
        cell.get("id")
        for cell in graph_root.findall("mxCell")
        if cell.get("edge") == "1"
    }

    vertices: list[tuple[str, str, tuple[float, float, float, float]]] = []
    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        # Skip edge labels (vertices whose parent is an edge cell)
        if cell.get("parent", "1") in edge_ids:
            continue
        geom = cell.find("mxGeometry")
        if geom is None:
            errors.append(f"{path}: vertex id={cell.get('id')} missing mxGeometry")
            continue
        try:
            x = float(geom.get("x", "0"))
            y = float(geom.get("y", "0"))
            w = float(geom.get("width", "0"))
            h = float(geom.get("height", "0"))
        except ValueError:
            errors.append(
                f"{path}: vertex id={cell.get('id')} has non-numeric geometry"
            )
            continue
        if w <= 0 or h <= 0:
            errors.append(
                f"{path}: vertex id={cell.get('id')} has non-positive geometry"
            )
        vertices.append(
            (cell.get("id", "<unknown>"), cell.get("parent", "1"), (x, y, w, h))
        )

    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            id1, parent1, box1 = vertices[i]
            id2, parent2, box2 = vertices[j]
            if parent1 != parent2:
                continue
            if has_overlap(box1, box2):
                errors.append(
                    f"{path}: overlap detected between vertices {id1} and {id2}"
                )

    for cell in graph_root.findall("mxCell"):
        if cell.get("edge") != "1":
            continue
        style = cell.get("style", "")
        if "edgeStyle=orthogonalEdgeStyle" not in style:
            errors.append(
                f"{path}: edge id={cell.get('id')} missing orthogonal style (edgeStyle=orthogonalEdgeStyle)"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate drawio files")
    parser.add_argument(
        "path", nargs="?", default="architecture/raw", help="File or folder to validate"
    )
    args = parser.parse_args()

    target = pathlib.Path(args.path)
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        return 2

    files = [target] if target.is_file() else sorted(target.glob("*.drawio"))
    if not files:
        print("No .drawio files found")
        return 0

    all_errors: list[str] = []
    for file in files:
        all_errors.extend(validate_file(file))

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print(f"Validation passed for {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
