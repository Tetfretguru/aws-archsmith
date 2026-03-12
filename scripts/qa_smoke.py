#!/usr/bin/env python3
"""Smoke QA runner for aws-archsmith local workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = ROOT / "architecture" / "specs" / "qa-smoke"
RAW_DIR = SMOKE_ROOT / "raw"
RENDER_INPUT_DIR = SMOKE_ROOT / "render-input"
RENDER_OUT_DIR = SMOKE_ROOT / "rendered"
REPORT_JSON = SMOKE_ROOT / "report.json"


CANONICAL_SERVICES = [
    "Route 53",
    "CloudFront",
    "WAF",
    "Application Load Balancer",
    "API Gateway",
    "Internet Gateway",
    "ECS",
    "Fargate",
    "EKS",
    "EC2",
    "Lambda",
    "AWS Batch",
    "Step Functions",
    "RDS",
    "Aurora",
    "PostgreSQL",
    "MySQL",
    "DynamoDB",
    "S3",
    "ElastiCache",
    "Redis",
    "OpenSearch",
    "Redshift",
    "EFS",
    "SQS",
    "SNS",
    "Kinesis",
    "MSK",
    "Amazon MQ",
    "EventBridge",
    "IAM",
    "KMS",
    "Secrets Manager",
    "Cognito",
    "Shield",
    "CloudWatch",
    "X-Ray",
    "CloudTrail",
    "NAT Gateway",
    "VPC Endpoint",
]


PARSER_VARIANTS = [
    "public alb, ecs service, rds postgres",
    "Route53 + cloudfront + api gateway + lambda + dynamodb",
    "internet gateway, ec2, redis, sns",
]


@dataclass
class CheckResult:
    check_id: str
    status: str
    detail: str


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"Command failed ({' '.join(cmd)}): {err}")
    return proc


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(8192)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def normalize_xml(path: Path) -> str:
    tree = ET.parse(path)
    root = tree.getroot()
    root.attrib.pop("modified", None)
    diagram = root.find("diagram")
    if diagram is not None:
        diagram.attrib.pop("id", None)
    return ET.tostring(root, encoding="unicode")


def list_service_cells(path: Path) -> tuple[int, list[str]]:
    tree = ET.parse(path)
    root = tree.getroot()
    graph_root = root.find("./diagram/mxGraphModel/root")
    if graph_root is None:
        return 0, ["missing graph root"]

    excluded = {"vpc", "public-subnet", "private-subnet"}
    total = 0
    missing_icon: list[str] = []

    for cell in graph_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        cid = cell.get("id", "")
        if cid in excluded:
            continue
        total += 1
        style = cell.get("style", "")
        if "shape=mxgraph.aws4." not in style:
            missing_icon.append(cell.get("value", cid))
    return total, missing_icon


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke QA suite")
    parser.add_argument("--skip-render", action="store_true", help="Skip Docker render checks")
    args = parser.parse_args()

    results: list[CheckResult] = []
    failures = 0

    def record(check_id: str, ok: bool, detail: str) -> None:
        nonlocal failures
        status = "PASS" if ok else "FAIL"
        results.append(CheckResult(check_id, status, detail))
        if not ok:
            failures += 1

    try:
        SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        RENDER_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        RENDER_OUT_DIR.mkdir(parents=True, exist_ok=True)

        for path in RAW_DIR.glob("*.drawio"):
            path.unlink()
        for path in RENDER_INPUT_DIR.glob("*.drawio"):
            path.unlink()
        for path in RENDER_OUT_DIR.glob("*.png"):
            path.unlink()
    except Exception as exc:
        print(f"Unable to initialize smoke directories: {exc}", file=sys.stderr)
        return 2

    for cmd, label in [
        (["python3", "--version"], "preflight-python"),
        (["docker", "--version"], "preflight-docker"),
        (["docker", "compose", "version"], "preflight-compose"),
    ]:
        try:
            out = run(cmd)
            record(label, True, (out.stdout.strip() or out.stderr.strip()).splitlines()[0])
        except Exception as exc:
            record(label, False, str(exc))

    try:
        unmapped: list[str] = []
        invalid: list[str] = []
        for service in CANONICAL_SERVICES:
            name = f"qa-smoke-icon-{slugify(service)}"
            file_path = RAW_DIR / f"{name}.drawio"
            run(
                [
                    "python3",
                    "scripts/generate_xml.py",
                    "--name",
                    name,
                    "--prompt",
                    service,
                    "--output-dir",
                    str(RAW_DIR),
                    "--icon-set",
                    "aws4",
                ]
            )
            val = run(["python3", "scripts/validate_drawio.py", str(file_path)], check=False)
            if val.returncode != 0:
                invalid.append(service)
                continue
            total, missing = list_service_cells(file_path)
            if total == 0 or missing:
                unmapped.append(service)
        ok = not unmapped and not invalid
        record("icons-coverage", ok, f"invalid={invalid}, unmapped={unmapped}")
    except Exception as exc:
        record("icons-coverage", False, str(exc))

    try:
        run(
            [
                "python3",
                "scripts/generate_xml.py",
                "--name",
                "qa-smoke-none",
                "--prompt",
                "public ALB, ECS service, RDS postgres, SQS",
                "--output-dir",
                str(RAW_DIR),
                "--icon-set",
                "none",
            ]
        )
        run(["python3", "scripts/validate_drawio.py", str(RAW_DIR / "qa-smoke-none.drawio")])
        record("icon-set-none", True, "generated and validated")
    except Exception as exc:
        record("icon-set-none", False, str(exc))

    parser_ok = True
    parser_details: list[str] = []
    for idx, prompt in enumerate(PARSER_VARIANTS, start=1):
        name = f"qa-smoke-parse-{idx}"
        try:
            run(
                [
                    "python3",
                    "scripts/generate_xml.py",
                    "--name",
                    name,
                    "--prompt",
                    prompt,
                    "--output-dir",
                    str(RAW_DIR),
                    "--icon-set",
                    "aws4",
                ]
            )
            run(["python3", "scripts/validate_drawio.py", str(RAW_DIR / f"{name}.drawio")])
            parser_details.append(f"{name}=ok")
        except Exception as exc:
            parser_ok = False
            parser_details.append(f"{name}=fail:{exc}")
    record("prompt-robustness", parser_ok, "; ".join(parser_details))

    try:
        deterministic_prompt = "public ALB, ECS service, RDS postgres, SQS"
        run(
            [
                "python3",
                "scripts/generate_xml.py",
                "--name",
                "qa-smoke-det-a",
                "--prompt",
                deterministic_prompt,
                "--output-dir",
                str(RAW_DIR),
                "--icon-set",
                "aws4",
            ]
        )
        run(
            [
                "python3",
                "scripts/generate_xml.py",
                "--name",
                "qa-smoke-det-b",
                "--prompt",
                deterministic_prompt,
                "--output-dir",
                str(RAW_DIR),
                "--icon-set",
                "aws4",
            ]
        )
        norm_a = normalize_xml(RAW_DIR / "qa-smoke-det-a.drawio")
        norm_b = normalize_xml(RAW_DIR / "qa-smoke-det-b.drawio")
        record("determinism", norm_a == norm_b, "normalized XML equal" if norm_a == norm_b else "normalized XML differ")
    except Exception as exc:
        record("determinism", False, str(exc))

    try:
        invalid_fixture = ROOT / "architecture" / "specs" / "qa-tests" / "invalid-root.drawio"
        gate_cmd = [
            "/bin/sh",
            "-lc",
            "python3 scripts/validate_drawio.py architecture/specs/qa-tests/invalid-root.drawio && "
            "docker compose -f docker/compose.yml run --rm renderer",
        ]
        proc = run(gate_cmd, check=False)
        ok = proc.returncode != 0 and "Container" not in (proc.stdout + proc.stderr)
        detail = f"rc={proc.returncode}, fixture_exists={invalid_fixture.exists()}"
        record("render-gate", ok, detail)
    except Exception as exc:
        record("render-gate", False, str(exc))

    rendered_hashes: dict[str, str] = {}
    if not args.skip_render:
        try:
            for file in RAW_DIR.glob("*.drawio"):
                shutil.copy2(file, RENDER_INPUT_DIR / file.name)
            run(
                [
                    "docker",
                    "compose",
                    "-f",
                    "docker/compose.yml",
                    "run",
                    "--rm",
                    "renderer",
                    "architecture/specs/qa-smoke/render-input",
                    "architecture/specs/qa-smoke/rendered",
                    "png",
                ]
            )
            pngs = sorted(RENDER_OUT_DIR.glob("*.png"))
            ok = len(pngs) > 0
            for png in pngs:
                rendered_hashes[png.name] = hash_file(png)
            record("render-smoke", ok, f"png_count={len(pngs)}")
        except Exception as exc:
            record("render-smoke", False, str(exc))
    else:
        record("render-smoke", True, "skipped")

    report = {
        "summary": {
            "total": len(results),
            "failed": failures,
            "passed": len(results) - failures,
        },
        "checks": [r.__dict__ for r in results],
        "render_hashes": rendered_hashes,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("QA Smoke Report")
    for r in results:
        print(f"- [{r.status}] {r.check_id}: {r.detail}")
    print(f"Report: {REPORT_JSON}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
