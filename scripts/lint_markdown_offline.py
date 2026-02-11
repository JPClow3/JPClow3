#!/usr/bin/env python3
"""Offline markdown checks for restricted environments.

Fallback when markdownlint-cli2 cannot be installed due network restrictions.
Validates a small subset of useful rules, including the one that broke CI
before (MD033/no-inline-html).
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# Match markdownlint-cli2 discovery style more closely (**/*.md).
FILES = sorted(
    p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "node_modules" not in p.parts
)

inline_html = re.compile(r"<\/?[A-Za-z][^>]*>")
trailing_ws = re.compile(r"[ \t]+$")

errors: list[str] = []

for file_path in FILES:
    in_code_fence = False
    rel_path = file_path.relative_to(ROOT)

    for i, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.rstrip("\n")

        # Toggle fenced code blocks to avoid false positives there.
        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue

        if trailing_ws.search(line):
            errors.append(f"{rel_path}:{i}: trailing whitespace")

        if not in_code_fence and inline_html.search(line):
            errors.append(
                f"{rel_path}:{i}: inline HTML detected (MD033 fallback): {line.strip()}"
            )

if errors:
    print("Offline markdown lint failed:\n")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print("Offline markdown lint passed for:")
for file_path in FILES:
    print(f"- {file_path.relative_to(ROOT)}")
