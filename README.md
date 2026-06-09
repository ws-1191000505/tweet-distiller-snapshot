# Research Event Distiller

## 中文说明

Research Event Distiller 是一个把公开 X/Twitter 发言转成**可证伪投资研究数据集**，并进一步沉淀为 **Codex skill** 的开源工程。

它最初是一个“单次抓取某位发布者截至当前可见推文”的 GitHub Actions 工具。后来扩展成完整流水线：

```text
公开推文
  -> 清洗语料
  -> 结构化 research events
  -> 市场价格富集
  -> forward return / drawdown / benchmark-relative 审计
  -> 人工图表复核
  -> 可复用投资研究 skill
```

这个项目按公开、免费或低成本环境设计：抓取、清洗、富集和分析可以在 GitHub Actions 上运行；X/Twitter cookies 和市场数据 API key 必须放在 GitHub Actions Secrets，不能提交进仓库。

## 项目解决什么问题

很多“大 V 蒸馏”只停留在总结层面：

- 他常提哪些主题；
- 他喜欢哪些股票；
- 他的写作风格是什么；
- 他有哪些经典观点。

这些有用，但不够严肃。对投资研究来说，更重要的问题是：

> 某条公开表达是在什么时间点发出的？当时价格是多少？后来是否跑赢 benchmark？最大回撤是多少？它是提前发现、继续确认，还是事后解释？

因此，这个项目的核心不是“总结一个人”，而是把公开表达转成可审计、可回测、可证伪的 research events。

## 创新点

这个工程的创新在于把定性文本和可验证市场数据连接起来：

```text
公开表达
  -> 时间戳
  -> 标的/行业/证据类型
  -> 入场参考价格
  -> forward returns
  -> benchmark-relative excess returns
  -> 人工复核标签
  -> 可迁移研究规则
```

以当前 Serenity AI/semi 数据集为例，最后沉淀出的不是“买某只股票”，而是一套研究方法：

```text
AI 需求冲击
  -> 产业链瓶颈层
  -> 稀缺技术/产能能力
  -> 未充分定价的受益者
  -> 多证据堆栈
  -> 信号阶段分类
  -> benchmark-relative 审计
```

这套方法也可以迁移到其他行业，比如电力电网、国防工业链、核燃料、CDMO、工业自动化、关键矿物等。

## 仓库结构

```text
.github/workflows/
  scrape.yml                     # GitHub Actions 抓取 X/Twitter 快照
  enrich-research-events.yml      # 构建 research events 并做市场数据富集

scrape.py                         # 使用 twscrape 做单次推文快照
prepare_distill_pack.py           # 生成语料包、提示词、topic candidates、evidence index
prepare_research_events.py        # 把推文转成结构化投资研究事件
enrich_research_events_twelvedata.py
                                  # 添加价格、forward returns、drawdown、benchmark returns
analyze_research_events.py        # 生成分组回测、候选规则、反例
make_manual_review_queue.py       # 生成需要人工图表复核的事件队列

skills/serenity-research-analyst/ # 从本项目沉淀出的 Codex skill
docs/PROJECT_OVERVIEW.md          # 面向公开展示的项目总览
docs/REPRODUCE_AND_BUILD_SKILL.md # 复现流水线并构建 skill 的操作指南
```

## 主要产物

核心结果位于：

```text
enriched-research-events/research_events/
```

重要文件包括：

- `enriched/01_research_events_enriched_twelvedata.csv`  
  主研究数据集，包含事件级市场富集。

- `analysis/01_backtest_summary.md`  
  分组表现摘要。

- `analysis/02_skill_candidates.md`  
  候选规则、弱模式和反信号。

- `analysis/03_manual_review_v1.md`  
  人工图表复核队列。

- `analysis/manual_review_labels.csv`  
  人工复核标签，例如 SIVE 被标记为 continuation confirmation，而不是低位首发。

- `analysis/04_serenity_bottleneck_methodology.md`  
  中文方法论：AI 基建瓶颈识别与跨行业泛化。

- `analysis/05_skill_trial_ai_infra_map_v1.md`  
  skill 试运行产物：AI 基建瓶颈地图。

- `analysis/06_skill_trial_cross_industry_power_grid.md`  
  跨行业泛化测试：电力电网。

- `analysis/07_skill_trial_report.md`  
  skill 测试报告。

## 当前数据集快照

在当前 Serenity 数据集中：

- 从公开推文中生成了 2,026 条结构化 research events。
- 最新公开 artifact 中有 600 行富集事件。
- 554 行有可用价格数据。
- SIVE 使用免费数据代理 `SIVEF` 定价。
- 最强可迁移证据组合是 `customer;supply_chain;earnings;rumor`。

部分研究结论：

| 模式 | 结论 |
| --- | --- |
| `SIVE` / `SIVEF` | 表现很强，但人工复核后定义为 continuation confirmation，不是低位首发。 |
| `AEHR` | 强事件簇，但需要合并同一推文/thread 的重复行，不能直接把样本数当独立信号。 |
| `customer;supply_chain;earnings;rumor` | 当前数据中最值得学习的证据堆栈。 |
| 宽泛 `ai_networking_optics` | 大主题整体不强，但内部存在强瓶颈，说明不能只按主题买入。 |
| 大盘/客户/背景票 | 常用于验证需求，不一定是直接 alpha 信号。 |

## Codex Skill

本项目沉淀出的 skill 位于：

```text
skills/serenity-research-analyst/
```

它教 Codex 做这些事：

- 分析带时间戳的投资研究事件；
- 区分 narrative logic、signal logic 和 risk logic；
- 识别 AI 基建瓶颈和未充分定价的受益者；
- 把事件分类为 early discovery、continuation confirmation、late validation、after-fact commentary 或 context-only；
- 将瓶颈型研究方法迁移到其他行业；
- 避免过拟合 ticker、大主题和重复推文行。

本地安装：

```powershell
Copy-Item -Recurse -Force `
  -LiteralPath ".\skills\serenity-research-analyst" `
  -Destination "$env:USERPROFILE\.codex\skills\serenity-research-analyst"
```

如果 Codex 没有立即识别，重启 Codex。

完整复现和 skill 构建流程见：

```text
docs/REPRODUCE_AND_BUILD_SKILL.md
```

## GitHub Actions 使用方式

### 1. 抓取公开推文

打开 `Actions -> Scrape X/Twitter snapshot -> Run workflow`。

输入项：

| Input | 示例 | 说明 |
| --- | --- | --- |
| `handles` | `aleabitoreddit` | X/Twitter 用户名，不需要 `@`。 |
| `limit` | `3200` | X/Twitter/twscrape 通常最多返回约 3200 条时间线推文。 |
| `include_replies` | `false` | 是否包含回复。 |
| `original_only` | `true` | 尽量排除回复、转推和引用推文。 |

Secrets：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `TWS_COOKIES` | 是 | X/Twitter cookie，通常形如 `auth_token=...; ct0=...`。 |
| `TWS_USERNAME` | 否 | twscrape 账号标签。 |
| `TWS_PROXY` | 否 | 可选代理。 |

### 2. 构建和富集 research events

打开 `Actions -> Enrich research events -> Run workflow`。

该 workflow 会生成结构化 research events，并使用市场数据进行价格富集。Twelve Data 免费层有严格速率限制，因此 workflow 提供了 sleep/pacing 控制。

常见 Secrets：

| Secret | 用途 |
| --- | --- |
| `TWELVEDATA_API_KEY` | Twelve Data 股票价格富集。 |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | 可选，旧版 Alpaca 富集脚本支持。 |

## 注意事项

- 本仓库用于公开、非保密研究。
- 不要提交 X/Twitter cookies、API keys、本地数据库、`.env` 或 twscrape 状态文件。
- 公开 GitHub Actions artifact 和日志应视为公开。
- X/Twitter 抓取受平台规则、账号状态、接口变化和所在地法律法规影响。
- 免费市场数据可能存在覆盖缺口、速率限制、代理代码、OTC 流动性和延迟问题。
- 本项目不构成投资建议；输出是研究假设、审计工具和 skill 规则。

## English Overview

Research Event Distiller is an end-to-end public research pipeline for turning an X/Twitter author's public posts into a falsifiable investment research dataset and, finally, a reusable Codex skill.

The project covers the full workflow:

```text
public tweets
  -> clean corpus
  -> structured research events
  -> market-data enrichment
  -> forward-return / drawdown audit
  -> manual review
  -> reusable investment-research skill
```

It is designed to run for free or near-free through GitHub Actions and free market-data tiers. Secrets such as X/Twitter cookies and market-data API keys must be stored in GitHub Actions Secrets, never committed to the repository.

## Why This Exists

Most "distill a great investor" workflows stop at summaries: themes, quotes, writing style, and favorite tickers. That is useful, but it is not enough for investment research.

This project makes the claims auditable:

- Every public expression becomes a timestamped research event.
- Each event can be tied to tickers, claim type, evidence type, and target role.
- Market prices are aligned to the event timestamp.
- Forward returns, drawdowns, runups, and benchmark-relative excess returns are measured.
- Strong patterns are separated from weak themes, duplicate tweets, and after-the-fact explanations.
- The final skill learns a research method, not a ticker list.

## What Is Innovative

The core innovation is the bridge between qualitative investor writing and falsifiable research events.

Instead of asking:

> What does this author believe?

this project asks:

> Which timestamped public claims survived price-path audit, benchmark comparison, and manual review, and what reusable research logic do they imply?

In the Serenity AI/semi dataset, the most useful lesson was not "buy a specific ticker." It was a method:

```text
AI demand shock
  -> constrained infrastructure layer
  -> scarce technical capability
  -> underpriced beneficiary
  -> evidence stack
  -> signal-stage classification
  -> benchmark-relative audit
```

This method can also be generalized to other industries such as power grid equipment, defense, CDMO, industrial automation, energy infrastructure, and consumer hardware supply chains.

## Data And Compliance Notes

- This repository is intended for public, non-confidential research.
- Do not commit X/Twitter cookies, API keys, local databases, `.env` files, or twscrape state.
- Public GitHub Actions artifacts and logs should be treated as public.
- X/Twitter scraping is unstable and subject to platform rules, account status, rate limits, and local law.
- Market-data free tiers can have coverage gaps, rate limits, stale prices, and proxy-symbol limitations.
- Nothing in this repository is investment advice. Outputs are research hypotheses and audit tools.

## Project Status

Current status:

- Snapshot scraping works through GitHub Actions.
- Research-event conversion works.
- Twelve Data enrichment works with free-tier pacing and proxy mappings.
- Analysis and manual-review queue generation work.
- `serenity-research-analyst` skill has been created, trialed, and locally installable.

Recommended next step:

1. Run another public-author dataset through the same pipeline.
2. Compare whether the bottleneck framework generalizes.
3. Keep adding manual review labels before treating any pattern as durable.
