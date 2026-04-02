---
name: skill-reflect
version: 1.0.0
description: Skill 失败后即时改进 -- 定位根因、评估影响、选择最确定性的修复层级、提案并执行
triggers:
  - /reflect
  - /skill-reflect
  - skill 失败了
  - skill 出错了
  - 这个 skill 有问题
  - 为什么 skill 没触发
---

# Skill Reflect -- 失败后即时改进

对出问题的 Skill 进行根因分析和修复，确保同一问题不再复发。

## 触发场景

以下任一情况出现时应使用本 skill：

- Skill 执行**失败**（报错、输出错误、行为异常）
- 用户**纠正**了 skill 行为（「不对，应该这样...」）
- 用户提供了**绕过** skill 限制的 workaround
- 你在执行中**临时修了** skill 的脚本或 prompt
- Skill **应触发但未触发** -- 用户手动做了 skill 本该处理的事（说明 trigger description 太窄）

## 执行流程

### Step 1: 定位根因

明确问题属于哪一类：

| 根因类型 | 典型表现 |
|----------|----------|
| 指令模糊 | Agent 理解偏差，做了错误操作 |
| 脚本 bug | 脚本报错或输出错误数据 |
| 参考文档过时 | 引用的 API/格式已变更 |
| 触发条件太窄 | 用户意图匹配但 skill 未激活 |
| 触发条件太宽 | 不相关场景误触发 |
| 环境/依赖问题 | 缺少工具、权限、token 等 |

### Step 2: 重读原文

**必须**重新读取目标 skill 的 SKILL.md 和相关脚本，确认 gap 确实存在。不凭记忆判断。

```bash
# 读取 SKILL.md
cat ~/.claude/skills/<skill-name>/SKILL.md

# 读取相关脚本
ls ~/.claude/skills/<skill-name>/scripts/
```

### Step 3: Impact Scan

扫描引用同一概念的文件，判断是否需要联动修改：

```bash
# 在 skills 目录中搜索关键词
grep -rl "<关键词>" ~/.claude/skills/

# 在 rules 目录中搜索
grep -rl "<关键词>" ~/.claude/rules/

# 在 CLAUDE.md 中搜索
grep "<关键词>" ~/.claude/CLAUDE.md
```

输出影响范围摘要：哪些文件引用了同一概念，是否需要联动修改。

### Step 4: Determinism Ladder

选择**最确定性**的修复层级（从上到下优先级递减）：

1. **改脚本** -- 能内置到 `scripts/` 自动执行？改脚本，删 SKILL.md 中对应的手动指令
2. **加 hook** -- 能用 hooks 确定性拦截？加 hook 配置
3. **改 SKILL.md** -- 需要 LLM 判断力？才写 SKILL.md 指令
4. **加 rule** -- 跨 skill 通用规则？写到 `~/.claude/rules/`

**反模式检测**：SKILL.md 写了「必须做 X」但 X 是确定性操作 --> 应内置到脚本，不应依赖 LLM 遵守。

### Step 5: 提案

向用户展示修复方案，必须包含：

- **改什么文件**：具体文件路径和修改内容
- **为什么能防复发**：修复如何消除根因
- **影响扫描结果**：Step 3 中发现的联动修改（如果有）
- **风险评估**：改动是否可能影响其他功能

### Step 6: 用户确认后执行

等待用户确认后再执行修改。不要自行修改 skill 文件。

## 升级规则

- 同一问题连续 reflect **2 次** --> 停止打补丁，向用户建议重新审视 skill 的基本设计思路
- 不同问题累计 reflect **3+ 次** --> 结构性问题，建议用户考虑重新设计而非继续修补

## 成熟度信号（判断是否建议发布）

当 skill 同时满足以下条件时，主动建议发布：

- 真实任务中成功使用 >= 3 次
- 最近 3 天（或连续 5 次成功执行）无 reflect 修复
- SKILL.md <= 300 行，frontmatter 完整
- 无硬编码路径或泄露的密钥

纯内部 skill（含组织特定逻辑）或用户已拒绝过发布的，不再建议。
