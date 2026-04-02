#!/usr/bin/env bash
# Render Excalidraw or Draw.io diagrams to PNG/SVG.
#
# Usage:
#   render-diagram.sh excalidraw input.excalidraw output.svg  [--local]
#   render-diagram.sh drawio     input.drawio     output.png
#
# Excalidraw: uses kroki.io by default, --local for Playwright rendering.
# Draw.io:    always uses local Playwright rendering (viewer.diagrams.net).

set -euo pipefail

FORMAT="${1:?Usage: render-diagram.sh <excalidraw|drawio> <input> <output> [--local]}"
INPUT="${2:?Missing input file}"
OUTPUT="${3:?Missing output file}"
LOCAL="${4:-}"

TMPDIR="${TMPDIR:-/tmp}"

render_excalidraw_kroki() {
  jq '{diagram_source: (. | tostring)}' "$INPUT" > "$TMPDIR/kroki-payload.json"
  if curl -sf -X POST -H "Content-Type: application/json" \
       --data-binary "@$TMPDIR/kroki-payload.json" \
       --max-time 30 \
       "https://kroki.io/excalidraw/svg" -o "$OUTPUT"; then
    local size
    size=$(wc -c < "$OUTPUT" | tr -d ' ')
    if [ "$size" -lt 100 ]; then
      echo "Warning: output too small (${size}B), rendering may have failed" >&2
      return 1
    fi
    echo "Rendered: $OUTPUT (${size}B via kroki.io)"
  else
    echo "kroki.io failed, falling back to local rendering..." >&2
    return 1
  fi
}

render_excalidraw_local() {
  cat > "$TMPDIR/render-excalidraw.html" << 'HTMLEOF'
<!DOCTYPE html>
<html><head>
<script type="module">
  import {exportToSvg} from "https://esm.sh/@excalidraw/excalidraw@0.18.0?alias=react:preact/compat,react-dom:preact/compat&deps=preact@10.25.4";
  const resp = await fetch('./diagram.json');
  const data = await resp.json();
  const svg = await exportToSvg({
    elements: data.elements,
    appState: {...(data.appState || {}), exportWithDarkMode: false},
    files: data.files || {}
  });
  document.body.appendChild(svg);
  document.title = 'RENDER_DONE';
</script>
</head><body style="background:#fff;margin:0;padding:20px"></body></html>
HTMLEOF
  cp "$INPUT" "$TMPDIR/diagram.json"
  npx agent-browser open "file://$TMPDIR/render-excalidraw.html" 2>/dev/null
  sleep 3
  npx agent-browser screenshot "$OUTPUT" 2>/dev/null
  npx agent-browser close 2>/dev/null
  echo "Rendered: $OUTPUT (local Playwright)"
}

render_drawio() {
  cat > "$TMPDIR/render-drawio.html" << 'HTMLEOF'
<!DOCTYPE html>
<html><head>
<script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>
</head><body style="background:#fff;margin:0;padding:20px">
<div class="mxgraph" style="max-width:100%">
  <div id="content" style="display:none"></div>
</div>
<script>
  fetch('./diagram.drawio').then(r=>r.text()).then(xml=>{
    document.getElementById('content').textContent = xml;
    setTimeout(() => { document.title = 'RENDER_DONE'; }, 2000);
  });
</script>
</body></html>
HTMLEOF
  cp "$INPUT" "$TMPDIR/diagram.drawio"
  npx agent-browser open "file://$TMPDIR/render-drawio.html" 2>/dev/null
  sleep 4
  npx agent-browser screenshot "$OUTPUT" 2>/dev/null
  npx agent-browser close 2>/dev/null
  echo "Rendered: $OUTPUT (local Playwright)"
}

case "$FORMAT" in
  excalidraw)
    if [ "$LOCAL" = "--local" ]; then
      render_excalidraw_local
    else
      render_excalidraw_kroki || render_excalidraw_local
    fi
    ;;
  drawio)
    render_drawio
    ;;
  *)
    echo "Unknown format: $FORMAT (expected: excalidraw or drawio)" >&2
    exit 1
    ;;
esac
