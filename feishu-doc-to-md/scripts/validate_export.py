#!/usr/bin/env python3
"""Validate a Feishu Markdown export produced by export_feishu_doc.py."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Feishu Markdown export and print a JSON summary.",
    )
    parser.add_argument("final_md", help="Path to the exported Markdown file")
    parser.add_argument(
        "--image-map",
        help="Optional path to image-map.tsv. Defaults to <stem>.assets/image-map.tsv next to the markdown file.",
    )
    return parser.parse_args()


def infer_image_map(final_md: Path) -> Path:
    return final_md.parent / f"{final_md.stem}.assets" / "image-map.tsv"


def load_unresolved_rows(image_map: Path) -> list[dict[str, str]]:
    if not image_map.exists():
        return []
    with image_map.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [
            row
            for row in reader
            if row.get("status") not in {"downloaded", "screenshotted"}
        ]


def main() -> int:
    args = parse_args()
    final_md = Path(args.final_md)
    image_map = Path(args.image_map) if args.image_map else infer_image_map(final_md)

    if not final_md.exists():
        raise SystemExit(f"Markdown file not found: {final_md}")

    text = final_md.read_text()
    lines = text.splitlines()
    image_lines = [idx for idx, line in enumerate(lines, start=1) if "![" in line]
    unresolved_rows = load_unresolved_rows(image_map)
    remote_image_refs = re.findall(r"!\[[^\]]*]\((?:<)?https?://", text)
    feishu_refs = re.findall(r"feishu://(?:image_token|board_token|board)/", text)
    top_cluster = bool(
        image_lines
        and len(image_lines) >= 6
        and sum(1 for line in image_lines if line <= 50) / len(image_lines) >= 0.8
    )

    summary = {
        "final_md": str(final_md),
        "image_map": str(image_map),
        "counts": {
            "image_refs": len(image_lines),
            "unresolved_rows": len(unresolved_rows),
            "feishu_refs": len(feishu_refs),
            "remote_image_refs": len(remote_image_refs),
        },
        "image_lines": image_lines[:50],
        "warnings": [],
        "unresolved": unresolved_rows[:20],
    }

    if top_cluster:
        summary["warnings"].append("image_refs_clustered_near_top")
    if not image_map.exists():
        summary["warnings"].append("image_map_missing")

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    has_errors = bool(unresolved_rows or feishu_refs or remote_image_refs)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
