---
name: excalidraw-diagram
description: 研发架构图制作规范。使用 Excalidraw 手绘风格程序化生成架构图和技术图表。
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: <需求描述>
---

# 研发制图规范

使用 Excalidraw 手绘风格，通过 Node.js 脚本程序化生成架构图、系统图等技术图表。

渲染方式：kroki.io 在线渲染，或 Playwright 本地渲染（离线 / 大文件）。

## 1. 布局原则

### 1.1 先定位，再连线

**模块位置是第一优先级。** 先根据模块之间的关系确定位置，再画连接箭头。

- 相关模块放在附近（如 EXTENSIONS 放在 AGENT RUNTIME 下方，因为它扩展 AR）
- 数据流方向决定主轴（如 Channel → Gateway → Agent 从左到右）
- 支撑模块放在被支撑模块下方（如 Infrastructure 在 Gateway 下方）

### 1.2 保持对称

追求三列、两行等网格化布局：

```
左列          中列          右列
CHANNELS    GATEWAY     AGENT RUNTIME     ← 核心数据流
NODES       INFRA       EXTENSIONS        ← 支撑 / 扩展
            CLIENTS                       ← 控制
```

同一行的模块顶部对齐，同一列的模块左边对齐。行间留 50-60px 间隙用于路由箭头。

### 1.3 保持整齐

- 模块框使用统一的圆角矩形（`roundness: { type: 3 }`）
- 子项等宽、等间距排列
- 避免散乱：所有元素应可被网格线覆盖

## 2. 箭头规则

### 2.1 箭头类型选择

根据场景选择合适的箭头类型：

- **直角拐弯箭头**（`roundness: null`）：适用于顺序流（A→B→C）、回退/重试路径等。拐角处是 90° 直角。
- **独立水平箭头**：适用于**一对多扇出**（如 Gateway → 多个 Node）。每条箭头从源框右侧对应目标 Y 位置出发，水平直连目标。**不要**用拐角箭头做扇出——所有线会重叠在同一条竖线上。

判断规则：如果多条箭头从同一个源出发到不同目标，且目标在同一列的不同 Y 位置，用独立水平箭头；否则用拐角箭头。

### 2.2 箭头路径格式

**禁止用对角线直连远距离模块。** 使用 L 型或 Z 型路径：

```javascript
// L 型：水平 → 垂直
points: [[0,0], [dx,0], [dx,dy]]

// Z 型：垂直 → 水平 → 垂直
points: [[0,0], [0,gap], [dx,gap], [dx,totalDy]]

// 反 L 型：垂直 → 水平
points: [[0,0], [0,dy], [dx,dy]]
```

### 2.3 在间隙中路由

箭头水平段和垂直段应走在模块之间的间隙空间内，**绝不穿越模块**。

- 行间间隙（~55px）用于水平路由
- 列间间隙（~60px）用于垂直路由
- 如果左侧间隙被占，绕右侧（或反之）

### 2.4 In / Out 分离

同一对模块之间的双向通信，用两条独立的单向箭头表示（不同 y 坐标错开），不要用一条双向箭头：

```
Channel ——In——→ Gateway     (y=325)
Channel ←—Out—— Gateway     (y=365)
```

### 2.5 箭头颜色

箭头颜色可跟随起点或终点模块的主色，用于视觉区分不同类型的连接。

## 3. 修改原则

### 3.1 最小修改

- 已经好的部分不动
- 读取现有文件 → 理解结构 → 做定点修改
- 不要因为一个小问题重新生成整张图

### 3.2 修改现有图的工作流

```
1. 读取 .excalidraw 文件，用脚本分析元素分布
2. 按空间坐标识别模块分组
3. 对目标模块做平移 / 缩放 / 增删元素
4. 写回文件，渲染验证
```

### 3.3 以参考文件为基础

如果用户提供了手动调整过的参考文件，应以它为基础做增量修改，不要重新生成。

## 4. Excalidraw 技术要点

### 4.1 基础属性

| 属性 | 值 | 说明 |
|------|-----|------|
| `fontFamily` | `8` | 代码友好等宽字体 |
| `roughness` | `1` | 微手绘风格 |
| `strokeWidth` | `2` | 统一线宽 |
| `roundness` | `{ type: 3 }` | 矩形圆角 |
| `roundness` | `{ type: 2 }` | 箭头圆角 |

### 4.2 Bound Text 陷阱（关键）

在矩形内放置居中文字时，**必须保证 ID 双向匹配**：

```javascript
const boxId = eid();
const lblId = eid();  // 预分配文字 ID

// 矩形引用文字
const box = {
  id: boxId,
  boundElements: [{ type: "text", id: lblId }],
  ...
};

// 文字引用矩形，且 id 必须是预分配的 lblId
const label = {
  id: lblId,           // 关键：必须与 boundElements 中的 id 一致
  containerId: boxId,  // 关键：反向引用矩形
  verticalAlign: "middle",
  ...
};
```

**常见错误：** `txt()` 函数内部调用 `eid()` 生成了新 ID，与矩形 `boundElements` 中预分配的 ID 不同 → 文字不显示。

**解决方案：** `txt()` 函数接受 `extra.id` 参数，传入预分配的 ID：

```javascript
function txt(x, y, w, h, text, fontSize, color, extra = {}) {
  return {
    id: extra.id || eid(),  // 优先使用传入的 ID
    type: "text",
    containerId: extra.containerId || null,
    ...
  };
}
```

### 4.3 模块分组样式

```javascript
// 模块外框：预设色板边框 + 预设淡色背景
rect(x, y, w, h, "#2f9e44", "#b2f2bb")  // 绿色模块（色板第3个）

// 模块标题：与边框同色、大字号
txt(x+10, y+8, w-20, 18, "MODULE NAME", 14, "#2f9e44")

// 模块副标题：黑色、小字号
txt(x+10, y+26, w-20, 13, "Description", 10, "#1e1e1e")

// 子项框：灰色边框 + 白色背景
labeledBox(x+16, y+48, w-32, 46, "Item", "Subtitle", "#ced4da", "#ffffff")

// 插件 / 扩展槽：虚线边框 + 浅黄色背景
box.strokeStyle = "dashed";
labeledBox(x+16, cy, w-32, 34, "+ Plugins", null, "#f08c00", "#ffec99")
```

### 4.4 色彩方案（美观优先）

**美观优先，自由选色。** 可以使用任意 hex 颜色值，不必局限于 Excalidraw 预设色板。选色原则：

1. **整体和谐**：同一张图的配色应有统一风格（如同色系渐变、互补色搭配）
2. **层次分明**：背景色用低饱和度（浅色），边框/文字用高饱和度（深色），形成清晰对比
3. **语义一致**：同一张图中相同角色的模块用相同颜色，不同角色用不同颜色
4. **克制用色**：一张图建议 3-5 种主色，不超过 7 种，避免花哨

推荐配色方案（可根据场景自由调整）：

**方案 A：现代科技风（默认）**

| 角色 | 边框色 (stroke) | 背景色 (fill) | 适用场景 |
|------|---------------|--------------|---------|
| 主要模块 | `#3B82F6` | `#EFF6FF` | Agent、核心服务 |
| 次要模块 | `#10B981` | `#ECFDF5` | Channel、数据源 |
| 强调模块 | `#F59E0B` | `#FFFBEB` | 告警、输入 |
| 危险/关键 | `#EF4444` | `#FEF2F2` | 错误、工具池 |
| 辅助模块 | `#8B5CF6` | `#F5F3FF` | 输出、客户端 |
| 中性模块 | `#6B7280` | `#F9FAFB` | 基础设施 |
| 子项边框 | `#E5E7EB` | `#FFFFFF` | 内部子项 |

也可以完全自定义颜色，只要遵循上述 4 条选色原则即可。

## 5. 渲染与验证流程

### 5.1 渲染方式

#### kroki.io 在线渲染（推荐）

```bash
# Excalidraw → SVG
jq '{diagram_source: (. | tostring)}' output.excalidraw > /tmp/kroki-payload.json
curl -s -X POST -H "Content-Type: application/json" \
  --data-binary @/tmp/kroki-payload.json \
  "https://kroki.io/excalidraw/svg" -o output.svg
```

注意事项：
- 请求体格式：`{"diagram_source": "<Excalidraw JSON 字符串>"}`
- 用 `jq '{diagram_source: (. | tostring)}'` 转换
- kroki 对 excalidraw **只支持 SVG**，不支持 PNG
- 大文件（>100KB）可能超时，改用本地 Playwright 渲染

#### SVG → PNG 转换

飞书等平台只支持位图（PNG/JPG），需要将 SVG 转为 PNG：

```bash
# 使用 rsvg-convert（需要 brew install librsvg）
# -z 2 表示 2 倍缩放，确保高清。飞书等平台显示时会自动缩放
rsvg-convert output.svg -z 2 -o output.png
```

完整流程：`kroki.io → SVG → rsvg-convert → PNG`

### 5.2 验证

渲染成 SVG/PNG 后，直接用 Read 工具查看图片文件（Read 支持读取图片）。无需 agent-browser。

### 5.3 验证检查清单

- [ ] 所有文字可见（无空白框 → 检查 bound text ID 匹配）
- [ ] 模块宽高足够，内部元素无溢出（文字、子项不超出外框边界）
- [ ] 模块对齐整齐
- [ ] 箭头不穿越模块
- [ ] 箭头标签位置合理
- [ ] 底部元素未被截断

## 6. 完整工作流

### 6.1 交互协议

**复杂图先确认方案再出图。** 对于 >3 个模块的图表：

1. 分析需求，列出模块清单和连接关系
2. 用文字描述布局方案（哪些模块在哪个位置，怎么连接）
3. **等用户确认后**再生成代码
4. 简单图（≤3 个模块）可直接生成

### 6.2 Excalidraw 工作流

```
用户需求 → 分析模块关系 → 确认布局方案（复杂图必须）
  → 写 .mjs 脚本（使用 references/excalidraw-codegen.md）
  → 运行生成 .excalidraw
  → kroki.io 渲染 SVG（失败则用本地 Playwright）
  → Read 工具查看 SVG 验证
  → 发现问题 → 修改脚本 → 重新生成
  → 确认无误 → 交付 .excalidraw + .svg
  → 清理临时 .mjs 脚本
```

详细的代码模板：`references/excalidraw-codegen.md`
