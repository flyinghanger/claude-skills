#!/usr/bin/env python3
"""Export a Feishu/Lark wiki or docx page into Markdown with local assets."""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


OPENAPI_BASE = "https://open.feishu.cn"
BOARD_FILE_BASE = "https://bytedance.larkoffice.com"
SHELL_ENV_PREFIX = (
    'export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"; '
    "export BYTECTL_NON_INTERACTIVE=true BYTECTL_DISABLE_AUTOVIEW=true;"
)

TEXT_KEYS = {
    "text",
    "heading1",
    "heading2",
    "heading3",
    "heading4",
    "heading5",
    "heading6",
    "bullet",
    "ordered",
    "code",
}


@dataclass
class HeadingContext:
    block_id: str
    text: str
    level: int


@dataclass
class MediaItem:
    index: int
    block_id: str
    block_type: int
    source_type: str
    source: str
    heading: Optional[HeadingContext]
    prev_text: str
    next_text: str
    alt: str
    target_rel: str = ""
    status: str = "pending"
    reason: str = ""


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr)


def shell(cmd: str) -> str:
    proc = subprocess.run(
        ["zsh", "-lc", f"{SHELL_ENV_PREFIX} {cmd}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def ensure_prerequisites() -> None:
    if shutil.which("bytectl") is None:
        raise SystemExit("bytectl not found in PATH")


def get_openfeishu_user_token() -> str:
    return shell("bytectl -b -s openfeishu uat")


def get_openfeishu_apiinfo() -> Dict[str, object]:
    raw = shell("bytectl -c openfeishu apiinfo")
    return json.loads(raw)


def request_bytes(
    url: str,
    *,
    bearer: Optional[str] = None,
    cookie: Optional[str] = None,
    timeout: int = 30,
) -> Tuple[bytes, Dict[str, str]]:
    headers = {"User-Agent": "Mozilla/5.0"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        meta = {k.lower(): v for k, v in resp.headers.items()}
        return resp.read(), meta


def request_json(url: str, *, bearer: Optional[str] = None) -> Dict[str, object]:
    body, _ = request_bytes(url, bearer=bearer)
    return json.loads(body.decode())


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip().rstrip(".")
    name = re.sub(r"\s+", " ", name)
    return name or "untitled"


def normalize_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", r"\1", text)
    text = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def clean_alt_candidate(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"https?://\S+", "", text)
    return text.strip(" :-")


def build_alt_text(prev_text: str, heading_text: str, index: int, seq: int) -> str:
    candidate = clean_alt_candidate(prev_text)
    fallback = clean_alt_candidate(heading_text)
    if (
        not candidate
        or len(candidate) > 40
        or "{" in candidate
        or "}" in candidate
        or "[" in candidate
        or "]" in candidate
    ):
        candidate = fallback
    if not candidate:
        candidate = f"图片 {index}"
    if len(candidate) > 40:
        candidate = candidate[:40].rstrip() + "..."
    if seq > 1:
        candidate = f"{candidate} {seq}"
    return candidate


def slugify(text: str) -> str:
    text = re.sub(r'[\\/:*?"<>|]', " ", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:60] or "untitled"


def detect_extension(body: bytes, headers: Dict[str, str]) -> str:
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if body.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if body.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(body) >= 12 and body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return ".webp"
    if body.lstrip().startswith(b"<svg"):
        return ".svg"
    content_type = headers.get("content-type", "")
    if "png" in content_type:
        return ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "gif" in content_type:
        return ".gif"
    if "webp" in content_type:
        return ".webp"
    if "svg" in content_type:
        return ".svg"
    return ".bin"


def extract_elements_text(obj: object) -> str:
    parts: List[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "text_run" in node and isinstance(node["text_run"], dict):
                parts.append(node["text_run"].get("content", ""))
            elif "mention_doc" in node and isinstance(node["mention_doc"], dict):
                parts.append(node["mention_doc"].get("title", ""))
            elif "mention_user" in node and isinstance(node["mention_user"], dict):
                parts.append(node["mention_user"].get("name", ""))
            elif "reminder" in node and isinstance(node["reminder"], dict):
                parts.append(node["reminder"].get("text", ""))
            elif "equation" in node and isinstance(node["equation"], dict):
                parts.append(node["equation"].get("content", ""))
            elif "file" in node and isinstance(node["file"], dict):
                parts.append(node["file"].get("name", ""))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(obj)
    return "".join(parts).strip()


def block_direct_text(block: Dict[str, object]) -> str:
    for key in TEXT_KEYS:
        if key in block:
            return extract_elements_text(block[key])
    return ""


def resolve_doc(input_value: str, token: str) -> Tuple[str, str, str]:
    if re.match(r"^https?://", input_value):
        parsed = urllib.parse.urlparse(input_value)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "wiki":
            source_token = parts[1]
            node = request_json(
                f"{OPENAPI_BASE}/open-apis/wiki/v2/spaces/get_node?obj_type=wiki&token={source_token}",
                bearer=token,
            )
            docx_token = node["data"]["node"]["obj_token"]
            title = node["data"]["node"].get("title", "")
            return source_token, docx_token, title
        if len(parts) >= 2 and parts[0] == "docx":
            source_token = parts[1]
            return source_token, source_token, ""
        raise SystemExit(f"unsupported url path: {parsed.path}")
    return input_value, input_value, ""


def fetch_doc_title(docx_token: str, token: str) -> str:
    data = request_json(
        f"{OPENAPI_BASE}/open-apis/docx/v1/documents/{docx_token}",
        bearer=token,
    )
    return data["data"]["document"]["title"]


def fetch_markdown(docx_token: str, token: str) -> str:
    data = request_json(
        f"{OPENAPI_BASE}/open-apis/docs/v1/content?doc_token={docx_token}&doc_type=docx&content_type=markdown",
        bearer=token,
    )
    return data["data"]["content"]


def fetch_blocks(docx_token: str, token: str) -> List[Dict[str, object]]:
    page_token: Optional[str] = None
    items: List[Dict[str, object]] = []
    while True:
        url = f"{OPENAPI_BASE}/open-apis/docx/v1/documents/{docx_token}/blocks?page_size=500"
        if page_token:
            url += "&page_token=" + urllib.parse.quote(page_token)
        data = request_json(url, bearer=token)
        items.extend(data["data"]["items"])
        if not data["data"].get("has_more"):
            break
        page_token = data["data"]["page_token"]
    return items


def build_heading_positions(
    markdown_lines: List[str],
    heading_blocks: List[HeadingContext],
) -> List[Dict[str, object]]:
    positions: List[Dict[str, object]] = []
    search_start = 0
    for heading in heading_blocks:
        needle = normalize_text(heading.text)
        line_index = None
        for idx in range(search_start, len(markdown_lines)):
            line = markdown_lines[idx]
            match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if not match:
                continue
            if len(match.group(1)) != heading.level:
                continue
            if needle == normalize_text(match.group(2)):
                line_index = idx
                search_start = idx + 1
                break
        positions.append(
            {
                "block_id": heading.block_id,
                "line_index": line_index,
                "level": heading.level,
                "text": heading.text,
            }
        )
    return positions


def shift_heading_positions(
    heading_positions: List[Dict[str, object]],
    inserted_at: int,
    delta: int,
) -> None:
    for item in heading_positions:
        line_index = item.get("line_index")
        if line_index is not None and line_index >= inserted_at:
            item["line_index"] = line_index + delta


def find_section_end(
    heading_positions: List[Dict[str, object]],
    heading_block_id: str,
    total_lines: int,
) -> int:
    current_idx = None
    current_level = None
    for idx, item in enumerate(heading_positions):
        if item["block_id"] == heading_block_id:
            current_idx = idx
            current_level = item["level"]
            break
    if current_idx is None:
        return total_lines
    for next_item in heading_positions[current_idx + 1 :]:
        next_line = next_item.get("line_index")
        if next_line is not None and next_item["level"] <= current_level:
            return next_line
    return total_lines


def find_anchor_line(
    lines: List[str],
    start: int,
    end: int,
    anchor_text: str,
) -> Optional[int]:
    anchor_norm = normalize_text(anchor_text)
    if not anchor_norm:
        return None
    probes = [anchor_norm]
    if len(anchor_norm) > 18:
        probes.append(anchor_norm[:32])
    if len(anchor_norm) > 10:
        probes.append(anchor_norm[:18])
    for idx in range(max(start, 0), min(end, len(lines))):
        line_norm = normalize_text(lines[idx])
        if line_norm and any(probe and probe in line_norm for probe in probes):
            return idx
    return None


def wrap_md_path(path: str) -> str:
    return f"<{path}>" if " " in path else path


def insert_media_lines(
    markdown: str,
    media_items: List[MediaItem],
    heading_positions: List[Dict[str, object]],
) -> str:
    lines = markdown.splitlines()
    global_cursor = 0
    fallback_lines: List[str] = []

    for item in media_items:
        if item.status != "downloaded":
            continue
        md_line = f"![{item.alt}]({wrap_md_path(item.target_rel)})"
        insertion_at: Optional[int] = None
        section_start = global_cursor
        section_end = len(lines)

        if item.heading:
            for heading in heading_positions:
                if heading["block_id"] == item.heading.block_id and heading.get("line_index") is not None:
                    section_start = max(global_cursor, heading["line_index"] + 1)
                    section_end = find_section_end(heading_positions, item.heading.block_id, len(lines))
                    break

        if item.prev_text:
            anchor_line = find_anchor_line(lines, section_start, section_end, item.prev_text)
            if anchor_line is not None:
                insertion_at = anchor_line + 1
        if insertion_at is None and item.next_text:
            anchor_line = find_anchor_line(lines, section_start, section_end, item.next_text)
            if anchor_line is not None:
                insertion_at = anchor_line
        if insertion_at is None and item.heading:
            anchor_line = find_anchor_line(lines, global_cursor, len(lines), item.heading.text)
            if anchor_line is not None:
                section_end = find_section_end(heading_positions, item.heading.block_id, len(lines))
                insertion_at = min(max(anchor_line + 1, global_cursor), section_end)
        if insertion_at is None and section_end > section_start:
            insertion_at = section_end

        if insertion_at is None:
            fallback_lines.append(md_line)
            continue

        lines[insertion_at:insertion_at] = ["", md_line, ""]
        shift_heading_positions(heading_positions, insertion_at, 3)
        global_cursor = insertion_at + 3

    if fallback_lines:
        lines.extend(["", "## Images", ""])
        for line in fallback_lines:
            lines.extend([line, ""])

    return "\n".join(lines) + "\n"


def build_media_items(
    blocks: List[Dict[str, object]],
    title: str,
) -> Tuple[List[MediaItem], List[HeadingContext]]:
    block_map = {block["block_id"]: block for block in blocks}
    root_id = next(block["block_id"] for block in blocks if block["block_type"] == 1)
    ordered_blocks: List[Dict[str, object]] = []
    heading_blocks: List[HeadingContext] = []

    def walk(block_id: str, current_heading: Optional[HeadingContext]) -> Optional[HeadingContext]:
        block = block_map[block_id]
        block["_heading"] = current_heading
        direct_text = block_direct_text(block)
        if block["block_type"] in (3, 4, 5, 6):
            current_heading = HeadingContext(
                block_id=block_id,
                text=direct_text,
                level=block["block_type"] - 2,
            )
            block["_heading"] = current_heading
            heading_blocks.append(current_heading)
        block["_direct_text"] = direct_text
        ordered_blocks.append(block)
        for child_id in block.get("children", []):
            current_heading = walk(child_id, current_heading)
        return current_heading

    walk(root_id, None)

    media_items: List[MediaItem] = []
    heading_counters: Dict[str, int] = {}

    for idx, block in enumerate(ordered_blocks):
        if block["block_type"] not in (27, 43):
            continue
        heading = block.get("_heading")
        prev_text = ""
        next_text = ""
        for prev in reversed(ordered_blocks[:idx]):
            text = prev.get("_direct_text", "")
            if text:
                prev_text = text
                break
        for nxt in ordered_blocks[idx + 1 :]:
            text = nxt.get("_direct_text", "")
            if text:
                next_text = text
                break

        source_type = "image_token" if block["block_type"] == 27 else "board_token"
        source = block["image"]["token"] if block["block_type"] == 27 else block["board"]["token"]
        heading_text = heading.text if isinstance(heading, HeadingContext) else title
        heading_key = f"{source_type}:{heading_text}"
        heading_counters[heading_key] = heading_counters.get(heading_key, 0) + 1
        seq = heading_counters[heading_key]

        media_items.append(
            MediaItem(
                index=len(media_items) + 1,
                block_id=block["block_id"],
                block_type=block["block_type"],
                source_type=source_type,
                source=source,
                heading=heading if isinstance(heading, HeadingContext) else None,
                prev_text=prev_text,
                next_text=next_text,
                alt=build_alt_text(prev_text, heading_text, len(media_items) + 1, seq),
            )
        )

    return media_items, heading_blocks


def download_media(
    media_items: List[MediaItem],
    title: str,
    images_dir: Path,
    token: str,
    cookie: str,
    quiet: bool,
) -> None:
    name_counters: Dict[str, int] = {}
    total = len(media_items)

    for position, item in enumerate(media_items, start=1):
        try:
            if item.source_type == "image_token":
                errors: List[str] = []
                body = b""
                headers: Dict[str, str] = {}

                try:
                    url = f"{OPENAPI_BASE}/open-apis/drive/v1/medias/{item.source}/download"
                    body, headers = request_bytes(url, bearer=token, timeout=60)
                except Exception as exc:  # noqa: BLE001
                    errors.append(str(exc))

                if len(body) < 32:
                    cover_url = (
                        f"{BOARD_FILE_BASE}/space/api/box/stream/download/v2/cover/{item.source}/"
                        f"?fallback_source=1&height=1280&mount_node_token={item.block_id}"
                        "&mount_point=docx_image&policy=equal&width=1280"
                    )
                    try:
                        body, headers = request_bytes(cover_url, cookie=cookie, timeout=60)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(str(exc))
                        raise RuntimeError("; ".join(errors))
            else:
                url = f"{BOARD_FILE_BASE}/space/api/file/f/cdp-whiteboard-{item.source}~noop/"
                body, headers = request_bytes(url, cookie=cookie, timeout=60)
            if len(body) < 32:
                raise RuntimeError("empty_payload")

            ext = detect_extension(body, headers)
            base = slugify(item.heading.text if item.heading else title)
            prefix = "board" if item.source_type == "board_token" else "image"
            name_key = f"{prefix}:{base}"
            name_counters[name_key] = name_counters.get(name_key, 0) + 1
            filename = f"{item.index:02d}-{base}-{prefix}-{name_counters[name_key]:02d}{ext}"
            target = images_dir / filename
            target.write_bytes(body)
            item.target_rel = f"{title}.assets/images/{filename}"
            item.status = "downloaded"
            log(f"[{position}/{total}] downloaded {filename}", quiet)
        except Exception as exc:  # noqa: BLE001
            item.status = "unresolved"
            item.reason = str(exc)
            log(f"[{position}/{total}] unresolved {item.source_type}:{item.source} -> {item.reason}", quiet)


def write_image_map(path: Path, media_items: List[MediaItem]) -> None:
    lines = ["source_type\tsource\ttarget_rel\tstatus\tblock_id\treason"]
    for item in media_items:
        lines.append(
            "\t".join(
                [
                    item.source_type,
                    item.source,
                    item.target_rel,
                    item.status,
                    item.block_id,
                    item.reason,
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a Feishu/Lark wiki or docx page into Markdown with local assets.",
    )
    parser.add_argument("doc_input", help="Wiki/docx URL or plain token")
    parser.add_argument(
        "--output-dir",
        help="Directory to place the exported files. Defaults to ./feishu-exports/<source_token>.",
    )
    parser.add_argument("--doc-name", help="Override the output Markdown base name.")
    parser.add_argument("--quiet", action="store_true", help="Only emit the final JSON summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_prerequisites()

    token = get_openfeishu_user_token()
    apiinfo = get_openfeishu_apiinfo()
    cookie = json.loads(apiinfo["auth"])["cookie"]

    source_token, docx_token, wiki_title = resolve_doc(args.doc_input, token)
    title = sanitize_filename(args.doc_name or wiki_title or fetch_doc_title(docx_token, token))

    output_dir = Path(args.output_dir) if args.output_dir else Path("feishu-exports") / source_token
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_md_path = output_dir / f"{title}.raw.md"
    final_md_path = output_dir / f"{title}.md"
    assets_dir = output_dir / f"{title}.assets"
    images_dir = assets_dir / "images"
    image_map_path = assets_dir / "image-map.tsv"
    images_dir.mkdir(parents=True, exist_ok=True)

    log(f"Resolving document: {args.doc_input}", args.quiet)
    raw_markdown = fetch_markdown(docx_token, token)
    raw_md_path.write_text(raw_markdown)

    log("Loading document blocks", args.quiet)
    blocks = fetch_blocks(docx_token, token)
    media_items, heading_blocks = build_media_items(blocks, title)

    log(f"Downloading {len(media_items)} assets", args.quiet)
    download_media(media_items, title, images_dir, token, cookie, args.quiet)
    write_image_map(image_map_path, media_items)

    heading_positions = build_heading_positions(raw_markdown.splitlines(), heading_blocks)
    final_markdown = insert_media_lines(raw_markdown, media_items, heading_positions)
    final_md_path.write_text(final_markdown)

    counts = {
        "total": len(media_items),
        "downloaded": sum(1 for item in media_items if item.status == "downloaded"),
        "unresolved": sum(1 for item in media_items if item.status != "downloaded"),
    }
    print(
        json.dumps(
            {
                "title": title,
                "source_token": source_token,
                "docx_token": docx_token,
                "output_dir": str(output_dir),
                "raw_md": str(raw_md_path),
                "final_md": str(final_md_path),
                "assets_dir": str(assets_dir),
                "image_map": str(image_map_path),
                "counts": counts,
                "unresolved": [
                    {
                        "source_type": item.source_type,
                        "source": item.source,
                        "block_id": item.block_id,
                        "reason": item.reason,
                    }
                    for item in media_items
                    if item.status != "downloaded"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
