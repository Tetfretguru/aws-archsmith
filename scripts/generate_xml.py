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
    "route 53": "Route 53",
    "cloudfront": "CloudFront",
    "waf": "WAF",
    "alb": "Application Load Balancer",
    "load balancer": "Application Load Balancer",
    "api gateway": "API Gateway",
    "apigateway": "API Gateway",
    "vpc endpoint": "VPC Endpoint",
    "nat gateway": "NAT Gateway",
    "internet gateway": "Internet Gateway",
    "ecs": "ECS Service",
    "fargate": "Fargate Task",
    "ec2": "EC2",
    "eks": "EKS",
    "lambda": "Lambda",
    "batch": "AWS Batch",
    "step functions": "Step Functions",
    "eventbridge": "EventBridge",
    "rds": "RDS",
    "aurora": "Aurora",
    "postgres": "RDS PostgreSQL",
    "mysql": "RDS MySQL",
    "dynamodb": "DynamoDB",
    "s3": "S3",
    "elasticache": "ElastiCache",
    "redis": "ElastiCache Redis",
    "opensearch": "OpenSearch",
    "redshift": "Redshift",
    "efs": "EFS",
    "sqs": "SQS",
    "sns": "SNS",
    "kinesis": "Kinesis",
    "msk": "MSK",
    "mq": "Amazon MQ",
    "iam": "IAM",
    "kms": "KMS",
    "secrets manager": "Secrets Manager",
    "cognito": "Cognito",
    "shield": "Shield",
    "cloudwatch": "CloudWatch",
    "x-ray": "X-Ray",
    "xray": "X-Ray",
    "cloudtrail": "CloudTrail",
}

INGRESS = {
    "Route 53",
    "CloudFront",
    "WAF",
    "Application Load Balancer",
    "API Gateway",
    "Internet Gateway",
}
COMPUTE = {"ECS Service", "Fargate Task", "EC2", "EKS", "Lambda", "AWS Batch", "Step Functions"}
DATA = {
    "RDS",
    "Aurora",
    "RDS PostgreSQL",
    "RDS MySQL",
    "DynamoDB",
    "S3",
    "ElastiCache",
    "ElastiCache Redis",
    "OpenSearch",
    "Redshift",
    "EFS",
}
MESSAGING = {"SQS", "SNS", "Kinesis", "MSK", "Amazon MQ", "EventBridge"}
SECURITY = {"IAM", "KMS", "Secrets Manager", "Cognito", "Shield"}
NETWORK = {"NAT Gateway", "VPC Endpoint"}
OBSERVABILITY = {"CloudWatch", "X-Ray", "CloudTrail"}

AWS4_ICON_BY_SERVICE = {
    "Route 53": "route_53",
    "CloudFront": "cloudfront",
    "WAF": "waf",
    "Application Load Balancer": "application_load_balancer",
    "API Gateway": "api_gateway",
    "Internet Gateway": "internet_gateway",
    "ECS Service": "ecs_service",
    "Fargate Task": "fargate",
    "EC2": "ec2",
    "EKS": "eks",
    "Lambda": "lambda",
    "AWS Batch": "batch",
    "Step Functions": "step_functions",
    "EventBridge": "eventbridge",
    "RDS": "rds",
    "Aurora": "aurora",
    "RDS PostgreSQL": "rds_postgresql_instance",
    "RDS MySQL": "rds_mysql_instance",
    "DynamoDB": "dynamodb",
    "S3": "s3",
    "ElastiCache": "elasticache",
    "ElastiCache Redis": "elasticache_for_redis",
    "OpenSearch": "opensearch_service_data_node",
    "Redshift": "redshift",
    "EFS": "efs_standard",
    "SQS": "sqs",
    "SNS": "sns",
    "Kinesis": "kinesis",
    "MSK": "msk_amazon_msk_connect",
    "Amazon MQ": "mq",
    "IAM": "identity_access_management_iam_roles_anywhere",
    "KMS": "key_management_service",
    "Secrets Manager": "secrets_manager",
    "Cognito": "cognito",
    "Shield": "shield",
    "CloudWatch": "cloudwatch",
    "X-Ray": "x_ray",
    "CloudTrail": "cloudtrail",
    "NAT Gateway": "nat_gateway",
    "VPC Endpoint": "vpc_endpoints",
}


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


def service_group(service: str) -> str:
    if service in INGRESS:
        return "ingress"
    if service in SECURITY:
        return "security"
    if service in NETWORK:
        return "network"
    if service in COMPUTE:
        return "compute"
    if service in MESSAGING:
        return "messaging"
    if service in DATA:
        return "data"
    if service in OBSERVABILITY:
        return "observability"
    return "compute"


def service_style(service: str, icon_set: str) -> str:
    if icon_set == "aws4":
        icon_key = AWS4_ICON_BY_SERVICE.get(service)
        if icon_key:
            return (
                f"shape=mxgraph.aws4.{icon_key};"
                "html=1;whiteSpace=wrap;align=center;verticalAlign=top;"
                "verticalLabelPosition=bottom;labelPosition=center;fontSize=11;spacingTop=4;"
            )

    group = service_group(service)
    palette = {
        "ingress": "strokeColor=#7A4E00;fillColor=#FFF3D6;",
        "security": "strokeColor=#6B1F1F;fillColor=#FDECEC;",
        "network": "strokeColor=#6F4B00;fillColor=#FFF7E6;",
        "compute": "strokeColor=#1B4F72;fillColor=#EAF4FF;",
        "messaging": "strokeColor=#5B4B8A;fillColor=#F2ECFF;",
        "data": "strokeColor=#1D6F42;fillColor=#EAFBF2;",
        "observability": "strokeColor=#5A5A5A;fillColor=#F3F3F3;",
    }
    return "rounded=1;whiteSpace=wrap;html=1;fontSize=12;" + palette[group]


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


def edge_anchor_style(source_box: tuple[float, float, float, float], target_box: tuple[float, float, float, float]) -> str:
    sx, sy, sw, sh = source_box
    tx, ty, tw, th = target_box
    scx = sx + sw / 2.0
    scy = sy + sh / 2.0
    tcx = tx + tw / 2.0
    tcy = ty + th / 2.0

    if abs(scx - tcx) >= abs(scy - tcy):
        if scx <= tcx:
            return "exitX=1;exitY=0.5;exitPerimeter=1;entryX=0;entryY=0.5;entryPerimeter=1;"
        return "exitX=0;exitY=0.5;exitPerimeter=1;entryX=1;entryY=0.5;entryPerimeter=1;"

    if scy <= tcy:
        return "exitX=0.5;exitY=1;exitPerimeter=1;entryX=0.5;entryY=0;entryPerimeter=1;"
    return "exitX=0.5;exitY=0;exitPerimeter=1;entryX=0.5;entryY=1;entryPerimeter=1;"


def add_edge(
    root: ET.Element,
    *,
    edge_id: str,
    source: str,
    target: str,
    parent: str = "1",
    source_box: tuple[float, float, float, float] | None = None,
    target_box: tuple[float, float, float, float] | None = None,
    label: str = "",
) -> None:
    style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;"
    if source_box and target_box:
        style += edge_anchor_style(source_box, target_box)

    edge = ET.SubElement(
        root,
        "mxCell",
        {
            "id": edge_id,
            "style": style,
            "edge": "1",
            "parent": parent,
            "source": source,
            "target": target,
            "value": label,
        },
    )
    ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})


def build_diagram(name: str, prompt: str, icon_set: str) -> ET.ElementTree:
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

    icon_mode = icon_set == "aws4"
    service_w = 96 if icon_mode else 220
    service_h = 96 if icon_mode else 60

    placements = {
        "ingress": {"parent": "1", "x": 30, "y": 60, "step": 118 if icon_mode else 90},
        "security": {"parent": "1", "x": 300, "y": 20, "step": 108 if icon_mode else 85},
        "observability": {"parent": "1", "x": 1160, "y": 20, "step": 108 if icon_mode else 85},
        "network": {"parent": "public-subnet", "x": 70, "y": 120, "step": 108 if icon_mode else 85},
        "compute": {"parent": "private-subnet", "x": 30, "y": 60, "step": 112 if icon_mode else 85},
        "messaging": {"parent": "private-subnet", "x": 30, "y": 330, "step": 108 if icon_mode else 75},
        "data": {"parent": "private-subnet", "x": 260, "y": 60, "step": 112 if icon_mode else 85},
    }
    counters: dict[str, int] = {key: 0 for key in placements}
    ids_by_group: dict[str, list[str]] = {key: [] for key in placements}
    boxes_by_id: dict[str, tuple[float, float, float, float]] = {}

    for svc in services:
        sid = slugify(svc)
        group = service_group(svc)
        slot = placements[group]
        row = counters[group]
        counters[group] += 1

        x = int(slot["x"])
        y = int(slot["y"]) + row * int(slot["step"])
        parent = str(slot["parent"])
        ids_by_group[group].append(sid)
        add_cell(
            root,
            cell_id=sid,
            value=svc,
            style=service_style(svc, icon_set),
            x=x,
            y=y,
            w=service_w,
            h=service_h,
            parent=parent,
        )
        boxes_by_id[sid] = (float(x), float(y), float(service_w), float(service_h))

    edge_n = 1

    def chain(ids: list[str]) -> None:
        nonlocal edge_n
        for i in range(len(ids) - 1):
            source = ids[i]
            target = ids[i + 1]
            add_edge(
                root,
                edge_id=f"e-{edge_n}",
                source=source,
                target=target,
                source_box=boxes_by_id.get(source),
                target_box=boxes_by_id.get(target),
            )
            edge_n += 1

    def bridge(source_ids: list[str], target_ids: list[str], label: str = "") -> None:
        nonlocal edge_n
        if not source_ids or not target_ids:
            return
        source = source_ids[-1]
        target = target_ids[0]
        add_edge(
            root,
            edge_id=f"e-{edge_n}",
            source=source,
            target=target,
            source_box=boxes_by_id.get(source),
            target_box=boxes_by_id.get(target),
            label=label,
        )
        edge_n += 1

    chain(ids_by_group["ingress"])
    chain(ids_by_group["compute"])
    chain(ids_by_group["messaging"])
    chain(ids_by_group["data"])

    bridge(ids_by_group["ingress"], ids_by_group["compute"], label="REQUEST")
    bridge(ids_by_group["ingress"], ids_by_group["messaging"], label="TRIGGER")
    bridge(ids_by_group["compute"], ids_by_group["messaging"], label="EVENT")
    bridge(ids_by_group["compute"], ids_by_group["data"], label="WRITE")
    bridge(ids_by_group["messaging"], ids_by_group["data"], label="INGEST")
    bridge(ids_by_group["security"], ids_by_group["compute"], label="AUTH")
    bridge(ids_by_group["observability"], ids_by_group["compute"], label="METRICS")

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
    parser.add_argument(
        "--icon-set",
        choices=["aws4", "none"],
        default="aws4",
        help="Service icon style set (default: aws4)",
    )
    args = parser.parse_args()

    diagram = build_diagram(args.name, args.prompt, args.icon_set)
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
