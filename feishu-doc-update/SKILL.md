---
name: feishu-doc-update
description: 将本地 Markdown 变更同步到飞书文档。有评论时新建标注副本，无评论时按变更规模选择直接更新或生成修订版。
triggers: 同步文档, sync doc, 更新飞书, 上传修改, 同步到飞书, update doc
version: 1.0.0
---

# 飞书文档更新 Skill

将本地 Markdown 变更同步到已关联的飞书文档。根据文档状态和变更规模自动选择策略：

```
有未解决评论？
  ├─ 是 → 新建完整副本，标注变更 block（保护评论上下文）
  └─ 否 → 变更 section ≤ 3？
              ├─ 是且无冲突 → 直接更新原文档
              └─ 否 → 生成修订版文档（仅含变更部分）
```

## 设计理念

首次上传后的飞书文档可能产生协作评论。评论锚定在特定段落/block 上，直接覆盖或追加会导致评论失去锚点或上下文错位。当文档存在评论时，新建一份完整副本并标注变更位置，让用户对照原文档手动合并，确保评论不受影响。

## 前置条件

- 本地 Markdown 文件已通过 `feishu-mapping.json` 关联到飞书文档
- mapping 文件路径：工作区下的 `docs/feishu-mapping.json`

## 执行流程

### Stage 1: 定位映射关系

从 `feishu-mapping.json` 中查找本地文件对应的飞书文档：

```json
{
  "local_file": "docs/plans/xxx.md",
  "feishu_doc_id": "CvPFdSO6go...",
  "feishu_wiki_token": "TDqzwQbl...",
  "title": "文档标题",
  "updated_at": "2026-03-17"
}
```

如果本地文件不在 mapping 中，询问用户是否首次上传（走 feishu-cli-import 流程）。

### Stage 2: 拉取云端文档

```bash
# 普通文档
feishu-cli doc export <doc_id> -o /tmp/feishu_cloud_<doc_id>.md

# 知识库文档（有 wiki_token 时）
feishu-cli wiki export <wiki_token> -o /tmp/feishu_cloud_<doc_id>.md
```

### Stage 3: 检查评论状态

```bash
feishu-cli comment list <doc_id> --type docx
```

判断是否存在**未解决的评论**（`is_solved: false`）。结果决定后续走哪条分支。

### Stage 4: Diff 分析

按 `##` 标题拆分为 section，逐段对比本地 vs 云端：

对比维度：
1. **新增 section**：本地有、云端无
2. **删除 section**：本地无、云端有（可能是云端新增的，标记为冲突）
3. **修改 section**：同标题但内容不同
4. **未变 section**：内容一致，跳过

**注意**：云端导出的 Mermaid 图表会变成 `[画板/Whiteboard](feishu://board/...)` 链接，这不算内容差异，diff 时应忽略包含 `feishu://board/` 的行。

### Stage 5a: 有评论 → 新建标注副本

条件：文档存在未解决的评论

**目的**：保留原文档的所有评论锚点，用户对照副本手动合并。

**Step 1**: 生成标注版 Markdown 到 `/tmp/annotated_<doc_id>_<timestamp>.md`

以云端文档为基础，**包含全部内容**，对变更的 section/block 添加标注：

```markdown
# {原标题}（标注副本 {YYYY-MM-DD HH:mm}）

> 原文档: {feishu_url}
> 本副本包含全部内容，变更处已用高亮块标注。请对照原文档手动合并。
> 变更统计：{N_modified} 处修改、{N_added} 处新增、{N_conflict} 处冲突

---

## 未变更的 section

（原样保留，无标注）

---

## 有变更的 section

> [!UPDATE] 此 section 已修改
> 原内容已替换为本地最新版本。

{本地最新内容}

---

## 本地新增的 section

> [!NEW] 此 section 为新增
> 原文档中不存在此内容。

{本地新增内容}

---

## 云端独有的 section（冲突）

> [!CONFLICT] 此 section 在本地已删除
> 云端存在但本地已删除，请确认是否在原文档中保留。

{云端内容}

---
```

标注规则：
- `> [!UPDATE]`：该 block 已被本地版本替换
- `> [!NEW]`：该 block 为本地新增
- `> [!CONFLICT]`：该 block 云端有但本地已删除

**Step 2**: 创建飞书文档

```bash
feishu-cli doc import /tmp/annotated_<doc_id>_<timestamp>.md --title "{原标题}（标注副本 {YYYY-MM-DD HH:mm}）"
```

添加权限并转移所有权：

```bash
feishu-cli perm add <new_doc_id> --doc-type docx --member-type email --member-id <your-email>@<your-domain>.com --perm full_access --notification
feishu-cli perm transfer-owner <new_doc_id> --doc-type docx --member-type email --member-id <your-email>@<your-domain>.com --notification
```

**Step 3**: 如果已有标注副本（mapping 中有 `annotated_doc_id`），更新已有副本：

```bash
feishu-cli doc import /tmp/annotated_<doc_id>_<timestamp>.md --document-id <annotated_doc_id>
```

**Step 4**: 更新 mapping：

```json
{
  "local_file": "docs/plans/xxx.md",
  "feishu_doc_id": "原文档ID",
  "annotated_doc_id": "标注副本ID",
  "annotated_url": "https://feishu.cn/docx/标注副本ID",
  "updated_at": "2026-04-01"
}
```

### Stage 5b: 无评论 + 少量修改 → 直接更新

条件：无未解决评论，且变更 section ≤ 3 个，且无云端独有 section（无冲突）

```bash
feishu-cli doc import <local_file> --document-id <doc_id>
```

更新 mapping 中的 `updated_at`。

### Stage 5c: 无评论 + 大量修改 → 生成修订版文档

条件：无未解决评论，且变更 section > 3 个或存在冲突

**Step 1**: 生成修订版 Markdown 到 `/tmp/revision_<doc_id>_<timestamp>.md`

修订版只包含变更部分：

```markdown
# [修订] {原标题} {YYYY-MM-DD HH:mm}

> 原文档: {feishu_url}
> 本次修订 {N} 个 section，请手动替换到原文档对应位置。

---

## [修改] {section 标题}

{本地最新内容}

---

## [新增] {section 标题}

{本地新增内容}

---

## [冲突] {section 标题}

> 该 section 在云端存在但本地已删除，请确认是否保留。

{云端内容}

---
```

**Step 2**: 创建飞书文档

```bash
feishu-cli doc import /tmp/revision_<doc_id>_<timestamp>.md --title "[修订] {原标题} {YYYY-MM-DD HH:mm}"
```

添加权限并转移所有权：

```bash
feishu-cli perm add <new_doc_id> --doc-type docx --member-type email --member-id <your-email>@<your-domain>.com --perm full_access --notification
feishu-cli perm transfer-owner <new_doc_id> --doc-type docx --member-type email --member-id <your-email>@<your-domain>.com --notification
```

**Step 3**: 如果已有修订版（mapping 中有 `revision_doc_id`），更新已有修订版：

```bash
feishu-cli doc import /tmp/revision_<doc_id>_<timestamp>.md --document-id <revision_doc_id>
```

**Step 4**: 更新 mapping：

```json
{
  "local_file": "docs/plans/xxx.md",
  "feishu_doc_id": "原文档ID",
  "revision_doc_id": "修订版文档ID",
  "revision_url": "https://feishu.cn/docx/修订版ID",
  "updated_at": "2026-04-01"
}
```

### Stage 6: 报告结果

**有评论 → 标注副本时**：
```
文档存在未解决评论，已生成标注副本：
  标注副本：{annotated_url}
  原文档：{feishu_url}

变更标注：
  - [UPDATE] {section1}（已修改）
  - [NEW] {section2}（新增）
  - [CONFLICT] {section3}（云端有、本地已删除）

请对照标注副本，在原文档中手动合并变更 block。
```

**无评论 → 直接更新时**：
```
已直接更新飞书文档：{feishu_url}
变更：{N} 个 section 已同步
```

**无评论 → 修订版时**：
```
变更较多（{N} 个 section），已生成修订版文档：
  修订版：{revision_url}
  原文档：{feishu_url}

修订内容：
  - [修改] {section1}
  - [新增] {section2}
  - [冲突] {section3}（云端有、本地已删除）

请在原文档中手动替换对应 block。
```

## 硬约束

- **本地只保留一份 md**：不创建本地副本或修订版文件
- **不删除云端内容**：任何分支都不自动删除原文档中的 block
- **评论保护优先**：有未解决评论时，禁止直接更新原文档，必须走标注副本
- **标注副本包含全文**：与修订版不同，标注副本包含文档全部内容，便于对照
- **复用副本/修订版**：同一原文档只维护一个标注副本和一个修订版，后续更新复用
- **Mermaid 豁免**：云端 Mermaid 转画板后的链接不视为内容差异
- **所有权转移**：新建文档必须转移所有权给 <your-email>@<your-domain>.com
