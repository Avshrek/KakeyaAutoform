#!/usr/bin/env python3
"""
diagnostic_engine.py — Reads the output of compiler_interface.py
and produces a structured diagnostic report with surgical fixes.

Usage:
    python compiler_interface.py --project-root .. --pretty | python diagnostic_engine.py
    
    or standalone:
    python diagnostic_engine.py --file PATH_TO_LEAN_FILE [--project-root PATH]
"""

import json
import sys
import os
import re
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════
# Known fix database: maps (category, pattern) → fix template
# ══════════════════════════════════════════════════════════════════════

KNOWN_FIXES = [
    # ── Typeclass: MeasureSpace for EuclideanSpace / WithLp / PiLp ──
    {
        "category": "typeclass",
        "pattern": r"MeasureSpace.*(EuclideanSpace|WithLp|PiLp|E3)",
        "diagnosis": (
            "Lean cannot synthesize a `MeasureSpace` instance for "
            "`EuclideanSpace ℝ (Fin n)` because it is `WithLp 2 (Fin n → ℝ)`, "
            "a structure wrapper that does NOT inherit `MeasureSpace` from the "
            "underlying Pi type."
        ),
        "required_imports": [
            "import Mathlib.MeasureTheory.Constructions.Pi",
            "import Mathlib.Analysis.Normed.Lp.MeasurableSpace",
        ],
        "code_fix": (
            "instance : MeasureSpace E3 where\n"
            "  volume := Measure.comap WithLp.ofLp volume"
        ),
    },

    # ── Typeclass: BorelSpace for WithLp ──
    {
        "category": "typeclass",
        "pattern": r"BorelSpace.*(WithLp|PiLp|EuclideanSpace)",
        "diagnosis": (
            "Lean cannot find a `BorelSpace` instance for `WithLp`/`PiLp`. "
            "Mathlib provides `PiLp.borelSpace` but it requires `Countable ι`, "
            "`∀ i, BorelSpace (X i)`, and `∀ i, SecondCountableTopology (X i)`."
        ),
        "required_imports": [
            "import Mathlib.Analysis.Normed.Lp.MeasurableSpace",
        ],
        "code_fix": "Ensure `import Mathlib.Analysis.Normed.Lp.MeasurableSpace` is present."
    },

    # ── Missing import: dimH / HausdorffDimension ──
    {
        "category": "import",
        "pattern": r"(dimH|hausdorffDim|HausdorffDimension)",
        "diagnosis": (
            "`dimH` is defined in `Mathlib.Topology.MetricSpace.HausdorffDimension`. "
            "This import is missing."
        ),
        "required_imports": [
            "import Mathlib.Topology.MetricSpace.HausdorffDimension",
        ],
        "code_fix": None,
    },

    # ── Missing import: angle / InnerProductGeometry ──
    {
        "category": "import",
        "pattern": r"(angle|InnerProductGeometry)",
        "diagnosis": (
            "`InnerProductGeometry.angle` is defined in "
            "`Mathlib.Geometry.Euclidean.Angle.Unoriented.Basic`."
        ),
        "required_imports": [
            "import Mathlib.Geometry.Euclidean.Angle.Unoriented.Basic",
        ],
        "code_fix": None,
    },

    # ── Missing import: cthickening / Thickening ──
    {
        "category": "import",
        "pattern": r"(cthickening|thickening|Thickening)",
        "diagnosis": (
            "`Metric.cthickening` is defined in "
            "`Mathlib.Topology.MetricSpace.Thickening`."
        ),
        "required_imports": [
            "import Mathlib.Topology.MetricSpace.Thickening",
        ],
        "code_fix": None,
    },

    # ── Syntax: ENNReal literal mismatch ──
    {
        "category": "type_mismatch",
        "pattern": r"ℝ≥0∞.*ℕ|Nat.*ENNReal",
        "diagnosis": (
            "A natural number literal like `3` needs to be coerced to `ℝ≥0∞` "
            "for comparison with `dimH`. Lean usually handles this automatically "
            "but may need an explicit cast."
        ),
        "required_imports": [],
        "code_fix": "Use `(3 : ℝ≥0∞)` or ensure `open scoped ENNReal` is present.",
    },
]


def match_fix(category: str, message: str):
    """Find the best matching known fix for a diagnostic."""
    for fix in KNOWN_FIXES:
        if fix["category"] == category and re.search(fix["pattern"], message):
            return fix
    return None


def generate_report(diagnostics_json: dict) -> str:
    """Generate a human-readable diagnostic report."""
    lines = []
    lines.append("=" * 72)
    lines.append("  LEAN 4 DIAGNOSTIC REPORT")
    lines.append("=" * 72)
    lines.append("")

    if diagnostics_json["build_success"]:
        lines.append("✅ BUILD SUCCEEDED")
        lines.append(f"   Exit code: {diagnostics_json['build_exit_code']}")
        lines.append(f"   Sorry count: {diagnostics_json['sorry_count']}")
        if diagnostics_json["sorry_count"] > 0:
            lines.append(f"   ⚠  {diagnostics_json['sorry_count']} declaration(s) use 'sorry'")
        lines.append("")
        lines.append("No errors to diagnose. The code type-checks successfully.")
        lines.append("=" * 72)
        return "\n".join(lines)

    lines.append("❌ BUILD FAILED")
    lines.append(f"   Exit code: {diagnostics_json['build_exit_code']}")
    lines.append(f"   Errors: {diagnostics_json['total_errors']}")
    lines.append(f"   Warnings: {diagnostics_json['total_warnings']}")
    lines.append(f"   Sorry count: {diagnostics_json['sorry_count']}")
    lines.append("")

    for i, err in enumerate(diagnostics_json.get("errors", []), 1):
        lines.append(f"── Error {i} ──────────────────────────────────────────────")
        lines.append(f"  File:     {err['file']}:{err['line']}:{err['col']}")
        lines.append(f"  Category: {err['category']}")
        lines.append(f"  Message:  {err['message'][:200]}")
        lines.append("")

        fix = match_fix(err["category"], err["message"])
        if fix:
            lines.append(f"  📋 Diagnosis:")
            lines.append(f"     {fix['diagnosis']}")
            lines.append("")
            if fix["required_imports"]:
                lines.append(f"  📦 Required Imports:")
                for imp in fix["required_imports"]:
                    lines.append(f"     {imp}")
                lines.append("")
            if fix["code_fix"]:
                lines.append(f"  🔧 Code Fix:")
                for fline in fix["code_fix"].split("\n"):
                    lines.append(f"     {fline}")
                lines.append("")
        elif err.get("suggested_fix"):
            lines.append(f"  🔧 Suggested Fix:")
            for fline in err["suggested_fix"].split("\n"):
                lines.append(f"     {fline}")
            lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)


def main():
    if not sys.stdin.isatty():
        # Reading piped JSON from compiler_interface.py
        data = json.load(sys.stdin)
    else:
        # Standalone mode: run compiler_interface and parse
        import subprocess
        import argparse
        parser = argparse.ArgumentParser(description="Lean 4 Diagnostic Report Generator")
        parser.add_argument("--project-root", default=os.path.join(os.path.dirname(__file__), ".."),
                            help="Path to the Lake project root")
        args = parser.parse_args()

        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "compiler_interface.py"),
             "--project-root", args.project_root, "--pretty"],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Failed to parse compiler output:", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

    report = generate_report(data)
    print(report)
    sys.exit(0 if data.get("build_success") else 1)


if __name__ == "__main__":
    main()
