---
name: searxng-search
version: 2.1
description: |
  通过私有 SearXNG 实例进行网络搜索，获取实时互联网信息。Claude Code 官方 WebSearch 的补充和增强，
  提供更丰富的搜索能力：多引擎聚合（Bing、Brave、Google 等 18+ 引擎）、分类搜索（通用、新闻、学术、开发者、视频）、
  时间范围过滤、翻页、JSON/CSV/RSS 多格式输出。无需 API Key，零配置开箱即用。
  当用户需要搜索互联网信息、查找最新资料、了解实时动态时使用此技能。
  触发场景包括但不限于：「搜一下」「查一下」「搜索」「search」「最新的 XXX」「XXX 是什么」
  「有没有关于 XXX 的资料」「帮我找找」「了解一下 XXX 的最新进展」「查查 XXX 的文档」
  「XXX 最新新闻」「最近 XXX 有什么动态」「今天有什么新闻」。
  当需要获取实时信息、验证事实、查找技术文档、了解新闻动态、搜索学术论文、查找开源项目时，
  都应该使用此技能。即使用户没有明确说「搜索」，只要任务需要互联网上的最新信息，也应主动使用。
  与 WebSearch 工具的区别：WebSearch 是单引擎搜索，本技能聚合多个引擎，结果更全面，
  且支持分类过滤、学术搜索、视频搜索等 WebSearch 不支持的能力。两者可以互补使用。
---

# SearXNG 网络搜索

通过自建 SearXNG 实例（`https://search.riba2534.cn`）执行互联网搜索，聚合多个搜索引擎的结果。

## 核心能力

- **多引擎聚合**：同时搜索 Bing、Brave、Google 等引擎，结果去重排序
- **分类搜索**：通用、IT/开发、学术、视频等不同类别
- **时间过滤**：按日/周/月/年筛选结果时效性
- **JSON API**：结构化返回，适合程序化处理
- **零认证**：无需 API Key，直接调用

## 搜索方式

```bash
# 基础搜索
~/.claude/skills/searxng-search/scripts/searx "关键词"

# 指定引擎和时间范围
~/.claude/skills/searxng-search/scripts/searx "关键词" --engines bing,brave

# 学术搜索
~/.claude/skills/searxng-search/scripts/searx "transformer attention" --category science

# 限制结果数
~/.claude/skills/searxng-search/scripts/searx "关键词" --limit 5

# 获取原始 JSON
~/.claude/skills/searxng-search/scripts/searx "关键词" --json
```

## 常用分类

| 分类 | 用途 |
|------|------|
| general | 通用网页搜索（默认） |
| science | 学术论文（arxiv、PubMed、Semantic Scholar） |
| news | 新闻 |
| it | 技术资源（GitHub、Docker Hub、crates.io） |
| packages | 包管理（npm、rubygems、pub.dev、pkg.go.dev） |
| repos | 代码仓库 |

## 环境变量

`SEARXNG_URL` — 覆盖默认实例地址（默认 `https://search.riba2534.cn`）
