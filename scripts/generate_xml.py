#!/usr/bin/env python3
"""Generate a deterministic, uncompressed Draw.io XML diagram from a prompt."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import uuid
import xml.etree.ElementTree as ET


SERVICE_MAP = {
    "route53": "Route 53",
    "cloudfront": "CloudFront",
    "waf": "WAF",
    "alb": "Application Load Balancer",
    "api gateway": "API Gateway",
    "apigateway": "API Gateway",
    "ecs": "ECS Service",
    "fargate": "Fargate Task",
    "ec2": "EC2",
    "eks": "EKS",
    "lambda": "Lambda",
    "rds": "RDS",
    "postgres": "RDS PostgreSQL",
    "mysql": "RDS MySQL",
    "dynamodb": "DynamoDB",
    "s3": "S3",
    "elasticache": "ElastiCache",
    "redis": "ElastiCache Redis",
    "sqs": "SQS",
    "sns": "SNS",
}

INGRESS = {"Route 53", "CloudFront", "WAF", "Application Load Balancer", "API Gateway"}
DATA = {"RDS", "RDS PostgreSQL", "RDS MySQL", "DynamoDB", "S3", "ElastiCache", "ElastiCache Redis"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "diagram"


def parse_services(prompt: str) -> list[str]:
    p = prompt.lower()
    seen: list[str] = []
    for key, label in SERVICE_MAP.items():
        if key in p and label not in seen:
            seen.append(label)

    if "RDS PostgreSQL" in seen and "RDS" in seen:
        seen.remove("RDS")
    if "RDS MySQL" in seen and "RDS" in seen:
        seen.remove("RDS")
    if "ElastiCache Redis" in seen and "ElastiCache" in seen:
        seen.remove("ElastiCache")

    if not seen:
        seen = ["Application Load Balancer", "ECS Service", "RDS PostgreSQL"]
    return seen


def add_cell(root: ET.Element, *, cell_id: str, value: str, style: str, x: int, y: int, w: int, h: int, parent: str = "1") -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": cell_id,
            "value": value,
            "style": style,
            "vertex": "1",
            "parent": parent,
        },
    )
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})


def add_edge(root: ET.Element, *, edge_id: str, source: str, target: str, parent: str = "1") -> None:
    edge = ET.SubElement(
        root,
        "mxCell",
        {
            "id": edge_id,
            "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
            "edge": "1",
            "parent": parent,
            "source": source,
            "target": target,
        },
    )
    ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})


def build_diagram(name: str, prompt: str) -> ET.ElementTree:
    services = parse_services(prompt)

    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "agent": "aws-archsmith",
            "version": "24.7.17",
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"id": str(uuid.uuid4())[:8], "name": "Page-1"})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1400",
            "dy": "900",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1600",
            "pageHeight": "1000",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    add_cell(
        root,
        cell_id="vpc",
        value="VPC",
        style="rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;strokeColor=#232F3E;fillColor=none;fontStyle=1;",
        x=240,
        y=140,
        w=1060,
        h=680,
    )
    add_cell(
        root,
        cell_id="public-subnet",
        value="Public Subnet",
        style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#8AA3B5;fillColor=#F5FAFF;",
        x=280,
        y=200,
        w=460,
        h=280,
        parent="vpc",
    )
    add_cell(
        root,
        cell_id="private-subnet",
        value="Private Subnet",
        style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#8AA3B5;fillColor=#F2F4F8;",
        x=760,
        y=200,
        w=500,
        h=520,
        parent="vpc",
    )

    base_style = "rounded=1;whiteSpace=wrap;html=1;strokeColor=#1B4F72;fillColor=#EAF4FF;fontSize=12;"
    ids: list[str] = []

    lane_y = 70
    ingress_x = 40
    compute_x = 360
    data_x = 760
    ingress_row = 0
    compute_row = 0
    data_row = 0

    for svc in services:
        sid = slugify(svc)
        ids.append(sid)
        if svc in INGRESS:
            x, y = ingress_x, lane_y + ingress_row * 100
            parent = "1"
            ingress_row += 1
        elif svc in DATA:
            x, y = data_x, 260 + data_row * 90
            parent = "private-subnet"
            data_row += 1
        else:
            x, y = compute_x, 260 + compute_row * 90
            parent = "private-subnet"
            compute_row += 1
        add_cell(root, cell_id=sid, value=svc, style=base_style, x=x, y=y, w=220, h=60, parent=parent)

    for idx in range(len(ids) - 1):
        add_edge(root, edge_id=f"e-{idx+1}", source=ids[idx], target=ids[idx + 1])

    return ET.ElementTree(mxfile)


def indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + "  " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = pad + "  "
        for child in element:
            indent(child, level + 1)
        if not element.tail or not element.tail.strip():
            element.tail = pad
    elif level and (not element.tail or not element.tail.strip()):
        element.tail = pad


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Draw.io XML from a prompt")
    parser.add_argument("--name", required=True, help="Diagram name (without extension)")
    parser.add_argument("--prompt", required=True, help="Natural language architecture instruction")
    parser.add_argument("--output-dir", default="architecture/raw", help="Output folder for .drawio")
    args = parser.parse_args()

    diagram = build_diagram(args.name, args.prompt)
    root = diagram.getroot()
    if root is None:
        raise RuntimeError("Failed to build XML root element")
    indent(root)
    output = f"{args.output_dir.rstrip('/')}/{slugify(args.name)}.drawio"
    diagram.write(output, encoding="utf-8", xml_declaration=True)
    print(f"Generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
