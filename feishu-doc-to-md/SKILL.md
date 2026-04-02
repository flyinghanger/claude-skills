---
name: feishu-doc-to-md
description: Export a Feishu/Lark wiki or docx URL/token into local Markdown with local image assets. Use when the user asks to convert 飞书/Lark 文档为 md, save a wiki/docx as Markdown, or preserve document images locally instead of leaving them remote.
allowed-tools: Bash, Read
metadata:
  short-description: Export Feishu docs to local Markdown
---

# feishu-doc-to-md

Export Feishu/Lark wiki or docx pages into Markdown plus local assets.

## When To Use

Trigger this skill when the user wants any of the following:

- A 飞书/Lark wiki or docx exported to `.md`
- Local image assets instead of remote document assets
- A repeatable Feishu-to-Markdown conversion flow

## Quick Start

Normalize `PATH` before running anything:

```bash
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
```

Run the main exporter:

```bash
python3 ~/.claude/skills/feishu-doc-to-md/scripts/export_feishu_doc.py "$DOC_URL_OR_TOKEN" --output-dir "$OUTPUT_DIR"
```

Common choices:

- Default export dir: omit `--output-dir`; the script uses `./feishu-exports/<source_token>/`
- Workspace docs dir: pass `--output-dir docs`
- Override the output file basename: add `--doc-name "Custom Name"`

The script prints a JSON summary with:

- `final_md`
- `raw_md`
- `assets_dir`
- `image_map`
- `counts`
- `unresolved`

## Validation

After every export, run:

```bash
python3 ~/.claude/skills/feishu-doc-to-md/scripts/validate_export.py "<final-md-path>"
```

Treat these as hard failures:

- unresolved rows in `image-map.tsv`
- remaining `feishu://...` placeholders
- remaining remote image refs like `![...](https://...)`

`validate_export.py` exits non-zero when any of those are present.

## Outputs

The exporter writes:

- `<output_dir>/<doc_name>.raw.md`
- `<output_dir>/<doc_name>.md`
- `<output_dir>/<doc_name>.assets/images/*`
- `<output_dir>/<doc_name>.assets/image-map.tsv`

## Auth Model

The scripted flow intentionally avoids `bytectl openfeishu uapi ...` as the primary transport because that path can block on interactive auth in agent sessions.

The exporter uses:

- `bytectl -b -s openfeishu uat` to fetch a fresh user token
- `bytectl -c openfeishu apiinfo` to read the current authenticated Lark session cookie
- direct HTTPS requests to Feishu OpenAPI and authenticated Lark file endpoints

Keep this model unless you have revalidated a better one end-to-end.

## Current Download Strategy

- `image_token`: download through OpenAPI `/open-apis/drive/v1/medias/<token>/download`
- `board_token`: download through authenticated Lark file URL `space/api/file/f/cdp-whiteboard-<token>~noop/`

Important:

- Board download through OpenAPI may return `404` in real docs even when board assets are visible in the document
- The current scripted cookie-based board path is the known-good path

## Troubleshooting

If the exporter fails before producing JSON:

- Check `bytectl` exists and is logged in
- Run `bytectl -b -s openfeishu uat`; it must return a token immediately
- Run `bytectl -c openfeishu apiinfo`; it must return JSON with `auth.cookie`

If assets are unresolved:

- Inspect `<doc_name>.assets/image-map.tsv`
- Report the unresolved rows and reasons back to the user
- Only reach for Playwright or screenshot fallback if the real export actually needs it

If you modify the exporter:

- Keep `SKILL.md` lean; put deterministic logic in scripts, not prose
- Re-run `validate_export.py`
- Re-run a real export smoke test on a known Feishu wiki/docx URL

## Files To Read

Read these only when needed:

- `scripts/export_feishu_doc.py`: main implementation
- `scripts/validate_export.py`: export checks

Do not expand this skill by pasting full algorithms into `SKILL.md`. Script-first is the intended maintenance model.
