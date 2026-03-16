#!/usr/bin/env python3
"""
compiler_interface.py — Lean 4 Auto-Formalization Diagnostic Engine

Runs `lake build` and captures structured error output for analysis.
Usage:
    python compiler_interface.py [--project-root PATH] [--target TARGET]

Output: JSON diagnostic report to stdout.
"""

import subprocess
import json
import re
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LeanDiagnostic:
    file: str
    line: int
    col: int
    severity: str          # "error" | "warning" | "info"
    category: str          # "typeclass", "import", "syntax", "unknown"
    message: str
    suggested_fix: Optional[str] = None


def classify_error(message: str) -> str:
    """Classify a Lean compiler error into a diagnostic category."""
    msg_lower = message.lower()

    if "failed to synthesize" in msg_lower or "typeclass" in msg_lower:
        return "typeclass"
    if "unknown identifier" in msg_lower or "unknown namespace" in msg_lower:
        return "import"
    if "unknown import" in msg_lower or "could not resolve import" in msg_lower:
        return "import"
    if "expected" in msg_lower and ("token" in msg_lower or "command" in msg_lower):
        return "syntax"
    if "type mismatch" in msg_lower:
        return "type_mismatch"
    if "application type mismatch" in msg_lower:
        return "application_type_mismatch"
    if "declaration uses 'sorry'" in msg_lower:
        return "sorry_warning"
    return "unknown"


def suggest_fix(category: str, message: str) -> Optional[str]:
    """Provide a surgical fix suggestion based on the error category."""
    if category == "typeclass":
        # MeasureSpace synthesis failure
        if "MeasureSpace" in message:
            if "EuclideanSpace" in message or "WithLp" in message or "PiLp" in message:
                return (
                    "Add an explicit MeasureSpace instance for the type:\n"
                    "  instance : MeasureSpace E3 where\n"
                    "    volume := Measure.comap WithLp.ofLp volume\n"
                    "Required imports:\n"
                    "  import Mathlib.MeasureTheory.Constructions.Pi\n"
                    "  import Mathlib.Analysis.Normed.Lp.MeasurableSpace"
                )
        if "MetricSpace" in message:
            return (
                "EuclideanSpace ℝ (Fin n) already has a MetricSpace instance "
                "via Mathlib.Analysis.InnerProductSpace.EuclideanDist. "
                "Make sure this import is present."
            )

    if category == "import":
        if "HausdorffDimension" in message or "dimH" in message:
            return "Add: import Mathlib.Topology.MetricSpace.HausdorffDimension"
        if "Thickening" in message or "cthickening" in message:
            return "Add: import Mathlib.Topology.MetricSpace.Thickening"
        if "angle" in message or "InnerProductGeometry" in message:
            return "Add: import Mathlib.Geometry.Euclidean.Angle.Unoriented.Basic"

    if category == "sorry_warning":
        return None  # Expected — proof not provided.

    return None


def parse_lean_output(output: str) -> list[LeanDiagnostic]:
    """Parse Lean 4 compiler output into structured diagnostics."""
    diagnostics = []

    # Lean 4 error format: <file>:<line>:<col>: <severity>: <message>
    # Messages can span multiple lines; a new diagnostic starts when
    # the pattern matches again.
    pattern = re.compile(
        r"^(.+?):(\d+):(\d+):\s*(error|warning|info):\s*(.*)",
        re.MULTILINE
    )

    matches = list(pattern.finditer(output))
    for i, m in enumerate(matches):
        # Capture multi-line message up to next diagnostic or end
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(output)
        continuation = output[start:end].strip()
        full_message = m.group(5)
        if continuation:
            full_message += "\n" + continuation

        category = classify_error(full_message)
        fix = suggest_fix(category, full_message)

        diagnostics.append(LeanDiagnostic(
            file=m.group(1),
            line=int(m.group(2)),
            col=int(m.group(3)),
            severity=m.group(4),
            category=category,
            message=full_message,
            suggested_fix=fix,
        ))

    return diagnostics


def run_lake_build(project_root: str, target: Optional[str] = None) -> tuple[int, str, str]:
    """Run `lake build` and capture output."""
    cmd = ["lake", "build"]
    if target:
        cmd.append(target)

    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.returncode, result.stdout, result.stderr


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lean 4 Diagnostic Engine")
    parser.add_argument("--project-root", default=os.getcwd(),
                        help="Path to the Lake project root")
    parser.add_argument("--target", default=None,
                        help="Specific Lake target to build")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print the JSON output")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not (project_root / "lakefile.toml").exists() and \
       not (project_root / "lakefile.lean").exists():
        print(json.dumps({"error": f"No lakefile found in {project_root}"}))
        sys.exit(1)

    print(f"Running lake build in {project_root}...", file=sys.stderr)
    returncode, stdout, stderr = run_lake_build(str(project_root), args.target)

    # Lean 4 outputs diagnostics to stderr
    combined_output = stdout + "\n" + stderr
    diagnostics = parse_lean_output(combined_output)

    # Filter out sorry_warnings for cleaner output
    errors = [d for d in diagnostics if d.severity == "error"]
    warnings = [d for d in diagnostics if d.severity == "warning" and d.category != "sorry_warning"]
    sorry_count = sum(1 for d in diagnostics if d.category == "sorry_warning")

    report = {
        "project_root": str(project_root),
        "build_exit_code": returncode,
        "build_success": returncode == 0,
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "sorry_count": sorry_count,
        "errors": [asdict(d) for d in errors],
        "warnings": [asdict(d) for d in warnings],
        "raw_output_tail": combined_output[-2000:] if len(combined_output) > 2000 else combined_output,
    }

    indent = 2 if args.pretty else None
    print(json.dumps(report, indent=indent))
    sys.exit(0 if returncode == 0 else 1)


if __name__ == "__main__":
    main()
