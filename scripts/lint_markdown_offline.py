#!/usr/bin/env python3
"""Offline markdown checks for restricted environments.

This is a lightweight fallback when markdownlint-cli2 cannot be installed due
network restrictions. It intentionally validates a small subset of rules,
including the one that broke CI before (MD033/no-inline-html).
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(ROOT.glob("*.md"))

inline_html = re.compile(r"<\/?[A-Za-z][^>]*>")
trailing_ws = re.compile(r"[ \t]+$")

errors: list[str] = []

for file_path in FILES:
    in_code_fence = False
    for i, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.rstrip("\n")

        # Toggle fenced code blocks to avoid false positives there.
        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue

        if trailing_ws.search(line):
            errors.append(f"{file_path.name}:{i}: trailing whitespace")

        if not in_code_fence and inline_html.search(line):
            errors.append(
                f"{file_path.name}:{i}: inline HTML detected (MD033 fallback): {line.strip()}"
            )

if errors:
    print("Offline markdown lint failed:\n")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print("Offline markdown lint passed for:")
for file_path in FILES:
    print(f"- {file_path.name}")
