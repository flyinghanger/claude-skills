# My Claude Code Skills

Personal skill collection for Claude Code.

## Categories

- [Feishu / Lark](#feishu--lark) — 飞书全套操作技能
- [Browser & Web](#browser--web) — 浏览器自动化、网页内容
- [Writing & Diagrams](#writing--diagrams) — 写作、图表生成
- [Skill Management](#skill-management) — Skill 的创建、安装、进化
- [Productivity](#productivity) — 效率工具
---

## Feishu / Lark

| Skill | Description |
|-------|-------------|
| [lark-shared](./lark-shared/) | 飞书 CLI 基础配置、认证登录、身份切换、权限管理 |
| [lark-base](./lark-base/) | 飞书多维表格：建表、字段、记录、视图、仪表盘、工作流 |
| [lark-calendar](./lark-calendar/) | 飞书日历：查看日程、创建会议、查询忙闲、推荐时段 |
| [lark-contact](./lark-contact/) | 飞书通讯录：查询人员、搜索员工、获取 open_id |
| [lark-doc](./lark-doc/) | 飞书云文档：创建、编辑、搜索文档，上传下载图片 |
| [lark-drive](./lark-drive/) | 飞书云空间：文件上传下载、目录管理、评论、权限 |
| [lark-event](./lark-event/) | 飞书事件订阅：WebSocket 实时监听消息/通讯录/日历变更 |
| [lark-im](./lark-im/) | 飞书即时通讯：收发消息、搜索聊天记录、管理群聊 |
| [lark-mail](./lark-mail/) | 飞书邮箱：起草、发送、回复、转发、搜索邮件 |
| [lark-minutes](./lark-minutes/) | 飞书妙记：获取会议录音、AI 总结、待办、逐字稿 |
| [lark-openapi-explorer](./lark-openapi-explorer/) | 探索飞书原生 OpenAPI，补充 CLI 未封装的接口 |
| [lark-sheets](./lark-sheets/) | 飞书电子表格：创建、读写、追加行、导出 |
| [lark-skill-maker](./lark-skill-maker/) | 将飞书 API 操作封装成可复用的 lark-cli Skill |
| [lark-task](./lark-task/) | 飞书任务：创建待办、跟踪状态、拆分子任务、分配成员 |
| [lark-vc](./lark-vc/) | 飞书视频会议：查询会议记录、获取会议纪要 |
| [lark-whiteboard](./lark-whiteboard/) | 飞书画板：绘制架构图、流程图、思维导图 |
| [lark-wiki](./lark-wiki/) | 飞书知识库：管理知识空间、节点层级、文档组织 |
| [lark-workflow-meeting-summary](./lark-workflow-meeting-summary/) | 工作流：汇总指定时间段内的会议纪要，生成结构化报告 |
| [lark-workflow-standup-report](./lark-workflow-standup-report/) | 工作流：生成今日/本周日程与未完成任务摘要 |
| [feishu-cli-auth](./feishu-cli-auth/) | 飞书 OAuth 认证与 User Access Token 管理 |
| [feishu-cli-bitable](./feishu-cli-bitable/) | 飞书多维表格全功能操作（feishu-cli 封装） |
| [feishu-cli-board](./feishu-cli-board/) | 飞书画板：创建画板、绘制图形 |
| [feishu-cli-chat](./feishu-cli-chat/) | 飞书会话浏览、消息互动与群聊管理 |
| [feishu-cli-doc-guide](./feishu-cli-doc-guide/) | 飞书文档创建前的兼容性检查（Mermaid/PlantUML 限制） |
| [feishu-cli-export](./feishu-cli-export/) | 飞书文档导出为 Markdown / PDF / Word |
| [feishu-cli-import](./feishu-cli-import/) | 从 Markdown 文件导入创建飞书文档 |
| [feishu-cli-msg](./feishu-cli-msg/) | 飞书消息发送（text / post / interactive 卡片等） |
| [feishu-cli-perm](./feishu-cli-perm/) | 飞书云文档权限管理：添加协作者、公开权限、分享密码 |
| [feishu-cli-read](./feishu-cli-read/) | 只读读取飞书云文档或知识库内容 |
| [feishu-cli-search](./feishu-cli-search/) | 搜索飞书云文档、消息和应用 |
| [feishu-cli-toolkit](./feishu-cli-toolkit/) | 飞书综合工具箱：表格、日历、任务、画板、搜索 |
| [feishu-cli-write](./feishu-cli-write/) | 向飞书文档写入内容，支持 Mermaid / PlantUML |
| [feishu-doc-to-md](./feishu-doc-to-md/) | 将飞书文档/知识库导出为本地 Markdown（含图片） |
| [feishu-doc-update](./feishu-doc-update/) | 将本地 Markdown 变更同步回飞书文档 |

---

## Browser & Web

| Skill | Description |
|-------|-------------|
| [agent-browser](./agent-browser/) | 浏览器自动化 CLI：导航、填表、点击、截图、数据抓取 |
| [browser-use](./browser-use/) | 基于 CDP 的无头浏览器自动化，用于测试和数据提取 |
| [reqable-capture](./reqable-capture/) | 通过 Reqable 抓包获取 Cookie / Token，解决登录态问题 |
| [youtube-transcript](./youtube-transcript/) | 提取 YouTube 视频字幕/逐字稿，支持带/不带时间戳 |

---

## Writing & Diagrams

| Skill | Description |
|-------|-------------|
| [content-pipeline](./content-pipeline/) | 内容生产流水线：写作、Fact Check、10 维评分、标准进化 |
| [writing-pipeline](./writing-pipeline/) | 写作评分与内容流水线，支持全流程串联 |
| [tech-doc-writing](./tech-doc-writing/) | 技术文档写作规范：自顶向下结构化表达 |
| [mermaid-diagrams](./mermaid-diagrams/) | 用 Mermaid 语法创建流程图、时序图、类图、ER 图等 |
| [excalidraw-diagram](./excalidraw-diagram/) | 用 Excalidraw 手绘风格生成架构图和技术图表 |
| [png-diagram](./png-diagram/) | 通过 HTML/SVG + Playwright 截图生成专业 PNG 图表 |
| [image-to-svg](./image-to-svg/) | 将架构图、流程图等图片转换为 SVG 矢量格式 |

---

## Skill Management

| Skill | Description |
|-------|-------------|
| [eat](./eat/) | 吸收外部知识（URL / 代码片段 / 文档），内化为 Skill 或规则 |
| [shit](./shit/) | 代谢掉过时、冗余、冲突的 Skill、Rule 和 Memory |
| [skill-creator](./skill-creator/) | 创建新 Skill、改进现有 Skill、运行评测和 benchmark |
| [skill-reflect](./skill-reflect/) | Skill 失败后即时改进：定位根因、选择修复层级、执行 |
| [install-skill](./install-skill/) | 从 GitHub 安装 Skill 到本地 Claude Code 配置 |
| [codify](./codify/) | 将上下文的核心要点、踩坑经验沉淀为结构化 Markdown 文档 |
| [ruminate](./ruminate/) | 回顾会话工作过程，提炼可沉淀的模式，改进 Skill 和规则 |

---

## Productivity

| Skill | Description |
|-------|-------------|
| [tmux-cli](./tmux-cli/) | 与其他 tmux 窗格中的 CLI Agent / 脚本通信 |
| [searxng-search](./searxng-search/) | 通过私有 SearXNG 实例搜索网络，支持多引擎、多格式输出 |
| [smart-ocr](./smart-ocr/) | 基于 macOS Vision 框架从图片提取文字 |
| [ip](./ip/) | 查看本机所有网络接口的 IP 地址（公网、VPN、局域网） |
| [daily-digest](./daily-digest/) | 从多个 RSS 源筛选 AI / 开发者内容，推送每日精选 |
| [init-project](./init-project/) | 长周期项目初始化：生成特性列表、进度日志、启动脚本 |
| [think-deeper](./think-deeper/) | 提示词优化助手：将模糊想法转化为清晰可执行任务 |
| [pua](./pua/) | 反懒惰模式：强制穷举所有可能方案后才能放弃 |
| [post-test-cleanup](./post-test-cleanup/) | 测试完成后的扫尾清理，防止测试消息残留消耗 token |
| [onchain-investigator](./onchain-investigator/) | 区块链地址链上数据调查分析（TRON / Ethereum 等） |
| [1password](./1password/) | 配置和使用 1Password CLI：读取/注入密钥 |


## Install

```bash
# Install a skill in Claude Code
/install-skill flyinghanger/agent-skills@<skill-name>
```

## License

MIT
