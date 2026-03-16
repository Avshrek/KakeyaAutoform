#!/usr/bin/env python3
"""
run_diagnostics.py — One-command diagnostic runner.

Usage:
    python Automation/run_diagnostics.py
    python Automation/run_diagnostics.py --project-root D:/kakeya_autoform
"""

import subprocess
import json
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root",
                        default=str(SCRIPT_DIR.parent),
                        help="Path to the Lake project root")
    args = parser.parse_args()

    # Step 1: Run compiler_interface.py
    print("=" * 72)
    print("  Step 1: Running lake build via compiler_interface.py ...")
    print("=" * 72)

    ci_result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "compiler_interface.py"),
         "--project-root", args.project_root, "--pretty"],
        capture_output=True, text=True
    )

    if not ci_result.stdout.strip():
        print("ERROR: compiler_interface.py produced no output.")
        print("STDERR:", ci_result.stderr)
        sys.exit(1)

    try:
        data = json.loads(ci_result.stdout)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse compiler output: {e}")
        print("RAW OUTPUT:", ci_result.stdout[:500])
        sys.exit(1)

    # Step 2: Feed into diagnostic_engine.py
    print()
    print("=" * 72)
    print("  Step 2: Generating diagnostic report ...")
    print("=" * 72)

    de_result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "diagnostic_engine.py")],
        input=ci_result.stdout,
        capture_output=True, text=True
    )

    print(de_result.stdout)
    if de_result.stderr:
        print("DIAGNOSTIC STDERR:", de_result.stderr, file=sys.stderr)

    # Step 3: Save outputs
    output_dir = SCRIPT_DIR
    with open(output_dir / "last_compiler_output.json", "w") as f:
        f.write(ci_result.stdout)
    with open(output_dir / "last_diagnostic_report.txt", "w") as f:
        f.write(de_result.stdout)

    print()
    print(f"  Saved: {output_dir / 'last_compiler_output.json'}")
    print(f"  Saved: {output_dir / 'last_diagnostic_report.txt'}")

    sys.exit(0 if data.get("build_success") else 1)


if __name__ == "__main__":
    main()
