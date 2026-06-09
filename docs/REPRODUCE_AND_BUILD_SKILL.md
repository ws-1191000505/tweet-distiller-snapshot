# Reproduce And Build Skill Guide

这份指南面向后来接手本项目的人类研究者或 AI agent。目标是从一个公开 X/Twitter 作者开始，逐步生成中间产物、构建可证伪研究事件数据库，并把有效模式沉淀为可复用 Codex skill。

本指南不依赖本项目开发过程中的对话上下文。

## 目标

最终产物不是“大 V 语录总结”，而是：

```text
public tweets
  -> structured research events
  -> market-enriched event table
  -> benchmark-relative audit
  -> manual review labels
  -> reusable research skill
```

## 前置条件

### 必要条件

- 一个 GitHub 仓库。
- GitHub Actions 可用。
- X/Twitter 登录 cookie，保存为 GitHub Actions Secret：`TWS_COOKIES`。
- Python 依赖：`requirements.txt`。

### 市场数据

推荐使用 Twelve Data：

- Secret 名称：`TWELVE_DATA_API_KEY`
- 免费层有速率限制，建议 `price_sleep_seconds >= 9`。

也可以使用其他数据源，但必须保留事件时间戳、入场参考价格、forward returns、drawdown 和 benchmark return。

## Step 1: 抓取公开推文

GitHub Actions:

```text
Actions -> Scrape X/Twitter snapshot -> Run workflow
```

常用参数：

```text
handles: aleabitoreddit
limit: 3200
include_replies: false
original_only: true
```

本地等价命令：

```powershell
python scrape.py --handles aleabitoreddit --limit 3200 --original-only --output-dir out
```

预期输出：

```text
out/
  tweets.jsonl
  tweets.csv
  corpus.md
  profile_prompt.md
  summary.json
```

判断标准：

- `summary.json` 中目标账号无严重错误。
- `tweets.csv` 有非零行数。
- 若抓取失败，优先检查 `TWS_COOKIES`、账号状态、X/Twitter 限流和 workflow 日志。

## Step 2: 生成初步语料包

本步骤用于定性理解作者内容，但不能替代事件级研究。

```powershell
python prepare_distill_pack.py tweet-distiller-snapshot.zip
```

预期输出：

```text
distill/
  00_pack_summary.json
  01_top_engagement.md
  02_timeline_chunks.md
  03_topic_candidates.md
  04_distill_prompt.md
  05_evidence_index.csv
```

使用原则：

- 可以用它理解主题、术语和写作习惯。
- 不要从这一步直接写 skill 规则。
- 投资研究规则必须进入 Step 3 之后的 research events 流程。

## Step 3: 构建 research events

```powershell
python prepare_research_events.py tweet-distiller-snapshot.zip
```

预期输出：

```text
research_events/
  01_research_events.jsonl
  01_research_events.csv
  02_research_event_schema.md
  03_human_review_queue.md
  04_research_event_prompt.md
```

事件字段至少应覆盖：

```text
source_url
author
published_at_utc
ticker
company
industry_node
claim_type
target_role
evidence_type
time_horizon
notes
```

判断标准：

- 每条事件必须有 `source_url` 和 `published_at_utc`。
- ticker 必须区分 focal beneficiary、customer、peer、comparison context。
- 不确定字段可以标为 `unclear`，但后续要视为 taxonomy gap。

## Step 4: 市场数据富集

Twelve Data:

```powershell
python enrich_research_events_twelvedata.py research_events/01_research_events.csv --sleep 9
```

预期输出：

```text
research_events/enriched/
  00_enrichment_report.json
  01_research_events_enriched_twelvedata.csv
  price_cache/
```

关键字段：

```text
entry_reference_price
forward_return_1d_pct
forward_return_5d_pct
forward_return_20d_pct
forward_return_60d_pct
forward_return_120d_pct
benchmark_forward_return_20d_pct
excess_forward_return_20d_pct
max_drawdown_after_signal_pct
max_runup_after_signal_pct
price_data_symbol
price_data_status
```

判断标准：

- `price_data_status=ok` 的行才可用于表现统计。
- `price_data_symbol != ticker` 时必须保留 proxy 说明。
- 免费数据源缺失不能被解释为负面表现。

## Step 5: 分析事件表现

```powershell
python analyze_research_events.py `
  --csv research_events/enriched/01_research_events_enriched_twelvedata.csv `
  --out-dir research_events/analysis `
  --min-sample 10
```

预期输出：

```text
research_events/analysis/
  00_analysis_manifest.json
  01_backtest_summary.md
  02_skill_candidates.md
  skill_candidate_patterns.csv
  group_by_*.csv
```

判断标准：

- 默认最小样本量：`n >= 10`。
- 优先使用 median、excess return、win rate、drawdown，而不是均值。
- 半导体/AI 基建默认 benchmark 为 SOXX。
- 非半导体行业必须更换为行业 ETF 或 peer basket。

## Step 6: 生成人工复核队列

```powershell
python make_manual_review_queue.py `
  --csv research_events/enriched/01_research_events_enriched_twelvedata.csv `
  --out research_events/analysis/03_manual_review_v1.md
```

人工复核要判断：

```text
是否第一信号 / 继续确认 / 事后解释
发帖前 20 个交易日是否已有前置涨幅
后续 5d / 20d / 60d 是否继续有效
是否跑赢 benchmark
是否存在 OTC / proxy / 流动性问题
同一 tweet/thread 是否产生重复 rows
```

建议标签：

```text
early_discovery
continuation_confirmation
late_validation
after_fact_commentary
context_only
invalid_or_unverified
```

人工标签建议保存为：

```text
research_events/analysis/manual_review_labels.csv
```

## Step 7: 判断哪些规则可以进入 skill

规则进入 skill 前必须满足：

```text
event-level traceability
priced rows
benchmark-relative evidence
sample-size discipline
manual review where needed
failure modes documented
```

可以进入 skill 的模式：

- 有清晰需求冲击。
- 能映射到具体瓶颈层。
- 有明确稀缺能力。
- ticker 是 focal beneficiary，而非纯客户或背景票。
- 证据堆栈强，例如 `customer + supply_chain + earnings/order + rumor/field_check`。
- 价格路径显示后续仍有 benchmark-relative value。

不能直接进入 skill 的模式：

- 只因作者提到某个 ticker。
- 只有宽泛 bullish thesis。
- 只有大主题，没有瓶颈层。
- 样本量太小。
- 同一 tweet/thread 重复行未聚类。
- 只看绝对收益，不看 benchmark。
- 无法解释失效条件。

## Step 8: 更新 skill

skill 位于：

```text
skills/serenity-research-analyst/
```

推荐更新顺序：

1. `references/validated-patterns.md`
   - 写入通过统计和人工复核的模式。

2. `references/failure-modes.md`
   - 写入反例、误判、数据问题和禁止学习的规则。

3. `references/ticker-taxonomy.md`
   - 写入 proxy、target_role 和行业节点问题。

4. `references/ai-infrastructure-bottleneck-method.md`
   - 写入 AI 基建场景的方法论。

5. `references/cross-industry-bottleneck-framework.md`
   - 写入跨行业迁移方法。

6. `SKILL.md`
   - 只放核心 workflow、触发条件和 reference 导航。

原则：

- 不要把大段数据塞进 `SKILL.md`。
- 详细案例放入 `references/`。
- skill 输出永远是 research framework / audit / rule draft，不是买卖建议。

## Step 9: 试运行 skill

最少做两个 trial：

1. 原始领域 trial
   - 例如生成 AI infrastructure bottleneck map。

2. 跨行业 trial
   - 例如 power grid、defense industrial base、nuclear fuel、CDMO。

trial 输出建议保存：

```text
research_events/analysis/05_skill_trial_ai_infra_map_v1.md
research_events/analysis/06_skill_trial_cross_industry_power_grid.md
research_events/analysis/07_skill_trial_report.md
```

通过标准：

- 能从 demand shock 推到 bottleneck layer。
- 能区分 focal beneficiary 与 context ticker。
- 能保留 benchmark 和 proxy caveat。
- 能主动指出 weak pattern 和 failure mode。
- 不输出 buy/sell recommendation。

## Step 10: 安装 skill

本地安装：

```powershell
Copy-Item -Recurse -Force `
  -LiteralPath ".\skills\serenity-research-analyst" `
  -Destination "$env:USERPROFILE\.codex\skills\serenity-research-analyst"
```

安装后重启 Codex，或在新线程中测试：

```text
使用 Serenity Research Analyst 分析一个新行业，输出需求冲击、瓶颈层、稀缺能力、候选受益者类型、证据堆栈、benchmark 和失效条件。
```

## 最终检查清单

发布前检查：

```text
[ ] README 说明项目目标和 GitHub Actions 使用方式
[ ] docs/PROJECT_OVERVIEW.md 解释项目创新
[ ] docs/REPRODUCE_AND_BUILD_SKILL.md 解释复现和 skill 构建
[ ] scrape workflow 可运行
[ ] enrich workflow 可运行
[ ] skill 文件夹包含 SKILL.md、agents/openai.yaml、references/、scripts/
[ ] 没有提交 cookies、API keys、.env、accounts.db、twscrape state
[ ] 生成产物如需公开，应通过 artifact/release/archive 管理
```

## 重要边界

- 本项目不是交易机器人。
- 本项目不构成投资建议。
- 公开推文抓取需遵守平台规则和所在地法律法规。
- 免费市场数据存在覆盖和速率限制。
- AI agent 可以生成候选研究规则，但人工复核仍然是高价值步骤。
