# Excalidraw JSON 代码生成模板

经过验证的 Node.js/MJS 代码模板，用于程序化生成 Excalidraw 架构图。

## 1. 基础工具函数

```javascript
import { writeFileSync } from 'fs';

const FF = 8;       // fontFamily: 代码友好字体
const ROUGH = 1;    // roughness: 微手绘
const ts = Date.now();
let _id = 0;
const eid = () => `e${++_id}`;
const seed = () => Math.floor(Math.random() * 2000000000);

// 所有元素共享的基础属性
const base = (extra = {}) => ({
  angle: 0, fillStyle: "solid", strokeWidth: 2, strokeStyle: "solid",
  roughness: ROUGH, opacity: 100, groupIds: [], frameId: null,
  roundness: null, seed: seed(), version: 1, versionNonce: seed(),
  isDeleted: false, updated: ts, link: null, locked: false,
  ...extra
});
```

## 2. 矩形

```javascript
function rect(x, y, w, h, stroke, bg, extra = {}) {
  return {
    id: eid(), type: "rectangle", x, y, width: w, height: h,
    strokeColor: stroke, backgroundColor: bg,
    ...base({ roundness: { type: 3 }, boundElements: [], ...extra })
  };
}
```

## 3. 文本

```javascript
// extra.id: 传入预分配 ID（用于 bound text）
// extra.containerId: 绑定到哪个容器
// extra.verticalAlign: "top" | "middle"
// extra.textAlign: "left" | "center" | "right"
function txt(x, y, w, h, text, fontSize, color, extra = {}) {
  return {
    id: extra.id || eid(),
    type: "text", x, y, width: w, height: h,
    strokeColor: color, backgroundColor: "transparent",
    ...base({ boundElements: null }),
    text, fontSize, fontFamily: FF,
    textAlign: extra.textAlign || "center",
    verticalAlign: extra.verticalAlign || "top",
    containerId: extra.containerId || null,
    originalText: extra.originalText || text,
    autoResize: true, lineHeight: 1.25
  };
}
```

## 4. 带标签的矩形框（核心模式）

```javascript
// 创建矩形 + 居中文字，正确处理 boundElements ID 匹配
// sub: 可选副标题（灰色小字）
function labeledBox(x, y, w, h, label, sub, stroke, bg) {
  const boxId = eid();
  const lblId = eid();  // 预分配文字 ID

  const box = {
    id: boxId, type: "rectangle", x, y, width: w, height: h,
    strokeColor: stroke, backgroundColor: bg,
    ...base({
      roundness: { type: 3 },
      boundElements: [{ type: "text", id: lblId }]  // 引用文字
    })
  };

  const els = [box];
  if (sub) {
    // 主标签（bound text，居中）
    els.push(txt(x+4, y+h/2-15, w-8, 17, label, 12, "#1e1e1e", {
      id: lblId, verticalAlign: "middle", containerId: boxId
    }));
    // 副标题（独立 text，不绑定）
    els.push(txt(x+4, y+h/2+3, w-8, 13, sub, 10, "#868e96"));
  } else {
    // 单行标签
    els.push(txt(x+4, y+h/2-8, w-8, 17, label, 12, "#1e1e1e", {
      id: lblId, verticalAlign: "middle", containerId: boxId
    }));
  }
  return { els, boxId };
}
```

## 5. 箭头

### 5.1 直线箭头

```javascript
function arrow(x1, y1, x2, y2, label, color, opts = {}) {
  const dx = x2 - x1, dy = y2 - y1;
  const id = eid();
  const els = [{
    id, type: "arrow", x: x1, y: y1,
    width: Math.abs(dx), height: Math.abs(dy),
    strokeColor: color, backgroundColor: "transparent",
    ...base({
      roundness: { type: 2 },
      points: [[0,0], [dx,dy]],
      startBinding: null, endBinding: null,
      startArrowhead: opts.bidir ? "arrow" : null,
      endArrowhead: "arrow",
      boundElements: null
    })
  }];
  if (label) {
    els.push(txt((x1+x2)/2-22, (y1+y2)/2-9, 44, 16, label, 11, color));
  }
  return els;
}
```

### 5.2 L 型弯折箭头

```javascript
// L 型：从 (x,y) 出发，先水平再垂直（或先垂直再水平）
function bendArrow(x, y, points, color, opts = {}) {
  const id = eid();
  return {
    id, type: "arrow", x, y,
    width: Math.max(...points.map(p => Math.abs(p[0]))),
    height: Math.max(...points.map(p => Math.abs(p[1]))),
    strokeColor: color, backgroundColor: "transparent",
    ...base({
      roundness: { type: 2 },
      points,
      startBinding: opts.startBinding || null,
      endBinding: opts.endBinding || null,
      startArrowhead: null,
      endArrowhead: "arrow",
      boundElements: null,
      elbowed: false
    })
  };
}

// 示例：从 Gateway 底部 (370,575) 左拐到 Nodes (145,630)
// 路径：下 25px → 左 225px → 下 30px
elements.push(bendArrow(370, 575, [
  [0, 0],        // 起点
  [0, 25],       // 垂直下到间隙
  [-225, 25],    // 水平左到目标上方
  [-225, 55],    // 垂直下到目标
], "#1971c2"));

// 示例：从 Clients 右侧 (660,770) 右拐上到 Gateway (660,575)
// 路径：右 22px → 上 195px → 左 22px
elements.push(bendArrow(660, 770, [
  [0, 0],
  [22, 0],       // 水平右到间隙
  [22, -195],    // 垂直上到目标
  [0, -195],     // 水平左回到对齐
], "#7950f2"));
```

## 6. 修改现有 Excalidraw 文件

### 6.1 空间分组 + 平移模式

```javascript
import { readFileSync, writeFileSync } from 'fs';

const data = JSON.parse(readFileSync('input.excalidraw', 'utf8'));

// 按空间坐标识别模块元素（不含箭头）
function classifyElement(el) {
  if (el.isDeleted || el.type === 'arrow') return null;
  const x = el.x, y = el.y;
  if (x >= -5 && x <= 270 && y >= 625 && y <= 725) return 'moduleA';
  if (x >= 710 && x <= 1020 && y >= 620 && y <= 820) return 'moduleB';
  return null;
}

// 计算平移量
const DELTA_A = { dx: 719, dy: -4 };  // moduleA 移到右侧
const DELTA_B = { dx: -715, dy: 0 };  // moduleB 移到左侧

// 应用平移
data.elements.forEach(el => {
  const mod = classifyElement(el);
  if (mod === 'moduleA') { el.x += DELTA_A.dx; el.y += DELTA_A.dy; }
  if (mod === 'moduleB') { el.x += DELTA_B.dx; el.y += DELTA_B.dy; }
});

// 删除需要重建的箭头
const oldArrow = data.elements.find(e => e.id === 'target-arrow-id');
if (oldArrow) oldArrow.isDeleted = true;

// 添加新箭头...
data.elements.push(/* new arrow */);

writeFileSync('output.excalidraw', JSON.stringify(data, null, 2));
```

### 6.2 分析现有文件结构

```javascript
// 列出所有矩形及附近文字
const rects = data.elements.filter(e => e.type === 'rectangle' && !e.isDeleted);
rects.forEach(r => {
  const texts = data.elements.filter(e =>
    e.type === 'text' && !e.isDeleted &&
    Math.abs(e.x - r.x) < 50 && Math.abs(e.y - r.y) < 50
  );
  const label = texts.length > 0 ? texts[0].text.substring(0, 40) : '(no text)';
  console.log(r.id, ':', r.x, r.y, r.width + 'x' + r.height, '|', label);
});

// 列出所有箭头及连接关系
const arrows = data.elements.filter(e => e.type === 'arrow' && !e.isDeleted);
arrows.forEach(a => {
  console.log(a.id, ':', a.x, a.y, 'points:', JSON.stringify(a.points));
  console.log('  color:', a.strokeColor);
  console.log('  start:', a.startBinding?.elementId, 'end:', a.endBinding?.elementId);
});
```

## 7. 渲染命令

```bash
# Excalidraw → SVG（kroki.io）
jq '{diagram_source: (. | tostring)}' diagram.excalidraw > /tmp/kroki-payload.json
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/kroki-payload.json \
  "https://kroki.io/excalidraw/svg" \
  -o diagram.svg

# 验证文件大小（正常应 >10KB）
wc -c diagram.svg
```

## 8. 文件输出模板

```javascript
writeFileSync('output.excalidraw', JSON.stringify({
  type: "excalidraw",
  version: 2,
  source: "https://excalidraw.com",
  elements,
  appState: { gridSize: null, viewBackgroundColor: "#ffffff" },
  files: {}
}, null, 2));
```
