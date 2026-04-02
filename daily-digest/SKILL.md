---
name: daily-digest
version: 0.5.0
description: |
  每日信息精选推送。从 19 个 RSS 源中筛选最值得深读的 AI/开发者内容，构建飞书卡片推送。
  触发词：/daily-digest、每日推送、信息精选、daily digest。
  支持运行时指令调整筛选方向，支持定时触发。
tags:
  - rss
  - digest
  - feishu
  - ai-news
  - information-diet
---

# Daily Digest — 每日信息精选推送

从 19 个 RSS 源中筛选最值得深读的内容，推送到飞书。只在有"值得中断"的内容时才推送，避免推送疲劳。

## 触发方式

- `/daily-digest` — 默认筛选
- `/daily-digest <指令>` — 带运行时指令，例如：
  - `/daily-digest 重点关注 LangGraph` → 筛选时优先匹配该话题
  - `/daily-digest 只看 AI Agent 方向` → 收窄范围
  - `/daily-digest 把 XX 新闻置顶` → 指定话题作为精选第一条
- 定时触发（通过 cron 或 /schedule）

如有运行时指令，在 Step 2 筛选时将其作为额外的优先级信号。

## 配置

运行前先读取本地配置文件 `~/.claude/skills/daily-digest/config.local.json`：

```json
{
  "push_target": {
    "user_id": "ou_xxx",
    "chat_ids": {
      "test": ["oc_test_group"],
      "prod": ["oc_prod_group"]
    }
  },
  "user_profile": {
    "name": "用户名",
    "interests": ["AI Agent", "LLM 应用开发"],
    "language": "zh-CN",
    "current_research": ["DeerFlow"]
  }
}
```

首次使用时如果该文件不存在，提示用户创建并填写自己的 user_id 和 chat_id，然后终止。

配置项说明：
- `push_target.user_id` — 飞书个人推送目标（`ou_` 开头）
- `push_target.chat_ids.test` — 测试群（调试时推送到这里）
- `push_target.chat_ids.prod` — 正式群（确认无误后推送到这里）
- 默认推送到 `prod` 群。加 `--test` 或运行时指令包含"测试"时推送到 `test` 群
- `user_profile.interests` — 用户关注方向，影响筛选优先级
- `user_profile.language` — 语言偏好。`zh-CN`（默认）时优先推荐中文源，英文内容仅在特别重大时才选入，卡片全部用中文。`en` 时不限语言
- `user_profile.current_research` — 当前研究方向，影响画像关联
- RSS 源: 见 `scripts/prefetch.py` 中的 FEEDS 字典
- 用户画像补充: 执行筛选前，也读取 `~/.claude/projects/*/memory/` 中的 user 类型记忆文件

## 工作流

### Step 1: 拉取 RSS 源

```bash
python3 ~/.claude/skills/daily-digest/scripts/prefetch.py
```

脚本输出 JSON 到 stdout，格式:
```json
{
  "fetched_at": "...",
  "total": 120,
  "articles": [
    {"source": "...", "title": "...", "link": "...", "date": "...", "summary": "..."},
    ...
  ],
  "github_trending": [
    {"repo": "owner/name", "description": "...", "language": "Python", "total_stars": "1234", "today_stars": "567"},
    ...
  ]
}
```

`github_trending` 是独立板块，取 top 3 展示，不参与文章筛选流程。

### Step 1.5: 数据评估与补充

检查 prefetch 结果，发现并补救数据缺口：

1. **源健康检查** — 统计每个源返回的文章数。如果某个 AI 类源返回 0 篇，按三级降级补充：
   - Level 1: web search 搜 `{源名} 最新` 补充
   - Level 2: 如果搜索结果太泛，直接 WebFetch 该源的网站首页
   - Level 3: 放弃该源，记录到步骤日志
2. **热点探测** — 如果同一事件/关键词出现在 3+ 个不同源中，说明是重大事件。对该事件执行一次 WebFetch 抓取原文，获取更完整的上下文用于后续筛选
3. **候选充实** — 对初筛后最有潜力的 3-5 篇候选文章，如果 RSS 摘要太短（<50 字），用 WebFetch 抓取原文前 500 字补充摘要，确保筛选依据充分

### 执行日志（贯穿全流程）

从 Step 1 开始，维护操作日志，每行格式 `[前缀] 动作 → 结果`。

示例：
```
[脚本] prefetch.py 并行抓取 → 19 源, 113 篇 + 5 repos (Jina AI: 0 篇)
[健康] Jina AI 0 篇 → 月更源，跳过
[画像] interests: AI Agent, 字节跳动相关 | memory: DeerFlow, info-diet
[过滤] 第一轮: 排除无关 (汽车/健身/营销) → 56 篇
[过滤] 第二轮: 值得中断评估 → 候选 6 篇
[✓] Deep Research 开源流水线 → Actionable (与 DeerFlow 直接相关)
[✓] ClawManager 上线 → Novel (Agent 编排新工具)
[✗] GLM-5.1 上线 → 增量更新，非全新事物
[✗] 小沓AI 营销产品 → 营销稿
[去重] 跨天去重: 历史 0 条，无重复
[精选] 最终 2 篇
```

规则：每行不超 80 字，结果用 → 连接，失败/降级/跳过要标注原因。`lark-cli` 推送动作不写入日志。

写入卡片时，日志用 `div` 元素，每行一个 icon + 灰色小字。前缀与 icon 对照：

| 前缀 | icon token | 示例 |
|------|-----------|------|
| `[脚本]` | `computer_outlined` | prefetch.py 抓取 |
| `[健康]` `[画像]` `[过滤]` `[去重]` | `robot_outlined` | 批量筛选/排除 |
| `[✓]` 入选 | `yes_outlined` | ✓ Deep Research → Actionable |
| `[✗]` 排除 | `recall_outlined` | ✗ GLM-5.1 → 增量���新 |
| `[精选]` | `todo_outlined` | 最终 3 篇 |
| `[搜索]` | `search_outlined` | 补充搜索 |
| `[抓取]` | `language_outlined` | 抓取原文确认质量 |
| `[热点]` | `announce_outlined` | "OpenClaw" 命中 3 源 |

已验证可用的 token：`computer_outlined` `robot_outlined` `language_outlined` `search_outlined` `edit_outlined` `right_outlined` `more_outlined` `yes_outlined` `recall_outlined` `todo_outlined` `announce_outlined` `export_outlined` `hide-toolbar_outlined`。不确定能用的用 `robot_outlined` 兜底。

div 写法：
```json
{ "tag": "div", "icon": { "tag": "standard_icon", "token": "computer_outlined", "color": "grey" }, "text": { "tag": "plain_text", "text_color": "grey", "text_size": "notation", "content": "prefetch.py → 19 源, 113 篇" } }
```

### Step 2: "值得中断"判断 + LLM 筛选

核心步骤。不是机械选 top N，而是判断是否存在**值得中断用户当前工作去阅读**的内容。

#### 2a: "值得中断"条件（至少满足一条）

1. **Novel（全新事物）** — 之前不存在的东西出现了（新框架、新产品、新研究），不是已有东西的小版本更新
2. **Actionable（读完就能用）** — 有具体的工具、方法、API、代码可以直接拿来用，不是纯观点输出
3. **Insightful（改变认知）** — 提供新视角、新数据或趋势洞察，读完会重新审视已有认知。例如：行业趋势分析、重大产品关停的复盘、赛道格局变化

三个标签。"知道就行"的行业动态（人事变动、融资消息）不占精选名额。

#### 2b: 筛选流程

1. 扫描所有候选文章的标题和摘要
2. 对每篇评估是否满足上述条件之一
3. 无任何文章满足 → **不推送**，输出 `[SKIP] 今日无值得中断的内容` 并结束
4. 有满足的 → 选出最佳 **1-3 条**（宁缺毋滥）
5. 同一事件多个源报道只留最优质的一篇

#### 2c: 链接验证与内容充实

1. **优先选非微信源** — 同一事件有 36kr、量子位(qbitai.com)、HuggingFace、TechCrunch 等非微信源时，优先用它们的链接
2. **微信链接找转载** — 链接是 `mp.weixin.qq.com` 时，web search 搜 `"文章标题"` 找同一篇的非微信转载。**必须验证日期是同一天**，避免搜到旧文
3. **找不到替代时自给自足** — 微信链接保留但推荐理由写 3 句以上，从 RSS 摘要和搜索结果提取核心内容，让用户不点链接也能获取 80% 的价值

推荐理由结构：第一句说这篇讲了什么，第二句说核心方法或发现，第三句说为什么和你相关。

#### 2d: 跨天去重

```bash
# 检查：输入候选文章 JSON，输出去重后的
echo '[{"link":"...","title":"..."}]' | python3 ~/.claude/skills/daily-digest/scripts/dedup.py check

# 推送成功后记录：
python3 ~/.claude/skills/daily-digest/scripts/dedup.py record "url" "title" "source"
```

去重逻辑：**仅 URL 精确匹配**。同一事件的新进展（不同 URL）不算重复。如果精选的文章是已推送事件的后续进展，在推荐理由中主动关联，例如：
> "3 天前推送过 LiteLLM 供应链攻击事件，本文是后续：攻击者身份已确认..."

历史保留 14 天后自动清理。记录文件 `push_history.json` 在 skill 目录下自动生成，不随 skill 分发。

**测试模式不记录历史**：推送到 `test` 群时（`--test` 或运行时指令含"测试"），跳过 `dedup.py record`，避免测试数据污染去重历史。

#### 2e: 优先信号

同等质量下的优先级因素：

- **源更新频率（月更 > 周更 > 日更）** — 低频源已做过筛选，文章质量更高。日更源之间：量子位 > 机器之心 > 新智元
- **用户兴趣** — `config.local.json` 的 `interests` + memory 中的 user 类型记忆。画像匹配度高的文章应加分，不能因为"用户已经知道"而排除。用户深度使用某工具 ≠ 不想看相关趋势分析，实践视角和行业分析是不同维度。"用户已了解"不是排除理由，"文章没有新信息"才是
- **来源多样性** — 1-3 篇精选尽量来自不同源

#### 2f: 排除项

- 纯营销/PR 稿、产品更新日志（除非重大版本）
- 和 AI/技术完全无关的内容（汽车、地产、健身、餐饮等）
- "又一个 X" — 同质化项目/产品（除非有本质差异）

**注意区分两种"无关"：** 和 AI 完全无关的内容（排除）vs AI 领域但不在用户具体方向的重大事件（保留）。用户关注 AI Agent / 开发工具链，但 AI 行业的重大事件（产品发布/关停、行业格局变化）即使不在具体方向内，也能拓宽赛道认知，应作为候选保留。

标题夸张但涉及重大事件的文章，先验证内容再决定是否排除。

### Step 3: 构建飞书消息卡片

将精选结果和筛选日志构建为飞书 Interactive Card JSON，写入 /tmp/daily_digest_card.json。

**必须使用 JSON 2.0**（`schema: "2.0"` + `body.elements`），否则 markdown 的 `###` 标题不会渲染。

卡片骨架：
```json
{
  "schema": "2.0",
  "config": { "wide_screen_mode": true, "enable_forward": true, "update_multi": true },
  "header": {
    "title": { "tag": "plain_text", "content": "AI Trending (YYYY-MM-DD)" },
    "subtitle": { "tag": "plain_text", "content": "{feeds_count} sources · {total} articles · {repos_count} repos" },
    "template": "wathet"
  },
  "body": {
    "elements": [
      { "tag": "collapsible_panel", "expanded": false, "header": { "title": { "tag": "plain_text", "text_color": "grey", "text_size": "notation", "content": "筛选过程" }, "icon": { "tag": "standard_icon", "token": "right_outlined", "color": "grey" }, "icon_position": "right", "icon_expanded_angle": 90 }, "border": { "color": "grey-300", "corner_radius": "6px" }, "vertical_spacing": "2px", "elements": ["... 日志 div 列表 ..."] },
      { "tag": "markdown", "content": "... 见下方模板 ..." }
    ]
  }
}
```

#### Markdown 内容模板

一整个 markdown 元素，用 `###` 做板块标题（JSON 2.0 下渲染为大字）：

```markdown
### 📌 精选文章

**[文章标题](verified_url)** 第一句说这篇讲了什么。第二句说核心发现或方法。第三句说为什么和你相关。
> 来源 · 日期 · <text_tag color='blue'>Actionable</text_tag>

**[文章标题](verified_url)** 第一句说这篇讲了什么。第二句说核心发现或方法。
> 来源 · 日期 · <text_tag color='green'>Novel</text_tag>

**[文章标题](verified_url)** 第一句说这篇讲了什么。第二句说改变了什么认知。
> 来源 · 日期 · <text_tag color='purple'>Insightful</text_tag>

---

### 🔥 GitHub Trending

- **[owner/repo](url)** ⭐ 总星标 (+今日新增)
一句话中文描述。语言。

---
*by {harness} · {model}*
```

签名中 `{harness}` 和 `{model}` 从当前运行环境获取，不写死。

#### 关键规则

- **JSON 2.0 不支持 `note` 元素** — 用 markdown 斜体 `*text*` 替代
- 标签颜色：`blue` = Actionable, `green` = Novel, `purple` = Insightful

### Step 4: 推送到飞书

从 `config.local.json` 读取推送目标：

```bash
lark-cli im +messages-send \
  --as bot \
  --chat-id {chat_id} \
  --msg-type interactive \
  --content "$(cat /tmp/daily_digest_card.json)"
```

## 注意事项

- prefetch 脚本只用 Python 标准库，不需要额外安装依赖
- 每个源最多取 10 篇，总量控制在 ~190 篇以内，避免 token 爆炸
- 7 天窗口覆盖周刊类源
