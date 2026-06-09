# Project Overview: From Public Tweets To A Research Skill

This document explains the full project in publication form. It is meant for GitHub readers who want to understand the engineering design, research methodology, and why the work is different from ordinary tweet scraping or LLM summarization.

## Problem

Investors often want to "distill" a strong public thinker from Twitter/X. Most workflows produce summaries:

- favorite sectors;
- repeated tickers;
- writing style;
- major themes;
- memorable quotes.

That is not enough for serious investment research. A public claim can sound smart and still be late, beta-driven, untradeable, or wrong.

The missing bridge is event-level falsifiability.

## Core Idea

Turn every meaningful public expression into a research event:

```text
source_url
author
published_at
ticker
claim_type
target_role
evidence_type
time_horizon
entry_reference_price
forward returns
drawdown / runup
benchmark-relative excess return
manual review label
```

Once claims become events, the workflow can separate:

- narrative insight;
- actual timing quality;
- benchmark-relative effectiveness;
- evidence quality;
- failure modes.

## Engineering Pipeline

### 1. Public Tweet Snapshot

`scrape.py` uses `twscrape` and GitHub Actions to collect a one-time snapshot of public X/Twitter posts.

Outputs:

- JSONL;
- CSV;
- Markdown corpus;
- summary metadata.

### 2. Distillation Pack

`prepare_distill_pack.py` turns raw posts into a more usable corpus:

- top engagement examples;
- timeline chunks;
- topic candidates;
- distillation prompt;
- evidence index.

This layer is useful for qualitative review but is not enough for investment validation.

### 3. Research Event Extraction

`prepare_research_events.py` converts posts into structured rows:

- ticker;
- company;
- industry node;
- claim type;
- evidence type;
- conviction;
- target role;
- source URL;
- timestamp.

This is the key shift from "summarize posts" to "audit claims."

### 4. Market Enrichment

`enrich_research_events_twelvedata.py` aligns event timestamps with price data:

- entry reference price;
- 1d / 5d / 20d / 60d / 120d forward returns;
- max drawdown;
- max runup;
- benchmark returns;
- benchmark-relative excess returns.

The free-data workflow supports proxy mapping, such as `SIVE -> SIVEF`, and pacing controls for Twelve Data rate limits.

### 5. Analysis

`analyze_research_events.py` groups events by ticker, price-data symbol, evidence type, claim type, industry node, market session, time horizon, and target role.

It produces candidate patterns, weak patterns, and contra-signals.

### 6. Manual Review

`make_manual_review_queue.py` selects events that need chart review.

Manual review is necessary because high forward returns can still be:

- late;
- duplicate/thread-inflated;
- driven by broad beta;
- explained by proxy-symbol issues;
- distorted by OTC liquidity.

### 7. Skill Construction

The final output is a Codex skill:

```text
skills/serenity-research-analyst/
```

The skill encodes a reusable method:

```text
demand shock
  -> bottleneck layer
  -> scarce capability
  -> underpriced beneficiary
  -> evidence stack
  -> signal-stage classification
  -> benchmark-relative audit
```

## Research Findings From The Current Dataset

The strongest insight is not that every AI/semi mention works. Some broad themes underperformed.

Important findings:

- `SIVE/SIVEF` was strong, but manual review labeled it as continuation confirmation, not early-bottom discovery.
- `customer;supply_chain;earnings;rumor` was the strongest reusable evidence stack.
- Broad `ai_networking_optics` was weak as a broad category even though sub-bottlenecks were strong.
- Some large-cap mentions were useful as demand validation but weak as direct signals.
- Duplicate rows from the same tweet/thread can overstate statistical confidence.

This forces the method to operate below the theme level.

## Methodological Contribution

The reusable research pattern is:

1. Identify a concrete demand shock.
2. Map the value chain.
3. Find the constrained layer.
4. Identify the scarce capability.
5. Locate underpriced beneficiaries.
6. Build a multi-source evidence stack.
7. Convert the claim into a timestamped event.
8. Audit the price path against a benchmark.
9. Classify the signal stage.
10. Preserve failure modes.

## Generalization Beyond AI

The same framework can be used outside AI/semi:

```text
demand shock -> industrial bottleneck -> scarce capacity -> underpriced beneficiary
```

Example sectors:

- power grid equipment;
- defense supply chains;
- CDMO and healthcare manufacturing;
- industrial automation;
- energy infrastructure;
- consumer hardware component cycles.

The benchmark must change by sector. SOXX is only appropriate for semiconductor or AI-infrastructure claims.

## What This Is Not

This project is not:

- a trading bot;
- investment advice;
- a guaranteed alpha engine;
- a private-data pipeline;
- a claim that any public author is always right.

It is a public, auditable workflow for transforming qualitative public writing into structured, testable research evidence.

## Suggested Citation

If you reuse this project, describe it as:

> An open workflow for converting public Twitter/X investment commentary into timestamped research events, market-enriched backtest tables, manual review labels, and reusable Codex skills.
