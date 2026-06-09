---
name: serenity-research-analyst
description: Analyze and distill Serenity-style AI/semi investment research from enriched tweet research events, especially when working with falsifiable event databases, forward returns, SOXX-relative performance, supply-chain bottleneck theses, ticker-level signal quality, AI infrastructure bottlenecks, cross-industry bottleneck beneficiary research, and creating or reviewing investment-research skill rules.
---

# Serenity Research Analyst

Use this skill to turn public Serenity-style tweet events into evidence-backed investment research patterns. Do not summarize the author as a personality. Convert claims into auditable research logic, separate narrative insight from trade effectiveness, and preserve failure modes.

## Core Workflow

1. Require event-level data before making claims.
   Use enriched event rows with `published_at_utc`, `ticker`, `claim_type`, `target_role`, `research_signal`, `entry_reference_price`, forward returns, drawdown, runup, benchmark returns, and `source_url`.

2. Filter for priced rows first.
   Treat `price_data_status != ok` as missing evidence. Do not infer performance for missing rows. Track proxy symbols such as `SIVE -> SIVEF`.

3. Prefer benchmark-relative evidence.
   For semiconductor and AI-infrastructure claims, prioritize `excess_forward_return_20d_pct` against `SOXX` over absolute return. Absolute gains during an AI beta rally are not enough.
   When applying the framework outside semiconductors, choose an industry benchmark or peer basket instead of SOXX.

4. Separate three layers.
   - Narrative logic: how the author maps AI demand to bottlenecks, suppliers, customers, capacity, materials, and small-cap beneficiaries.
   - Signal logic: whether a tweet-level event created excess return after the timestamp.
   - Risk logic: where the narrative failed, was late, relied on proxies, or only reflected broad beta.

5. Distinguish discovery from continuation confirmation.
   A strong case may occur after prior runup. Label it as early discovery, continuation confirmation, late validation, or after-the-fact commentary before turning it into a rule.

6. Cluster duplicate thesis events.
   Repeated rows from the same tweet, thread, or thesis cluster are not independent signals. Cluster before interpreting sample size.

7. Require sample-size discipline.
   Default minimum sample is 10 priced events for grouped statistics. Mark anything below that as exploratory.

8. Use medians and drawdowns.
   Report median return, median excess return, excess win rate, median max drawdown, median max runup, and sample size. Avoid relying on mean return alone.

9. Preserve source traceability.
   Keep representative `source_url` examples for every proposed rule. If a rule cannot be traced to events, do not add it to the skill.

## When Analyzing A Dataset

Run the bundled script when an enriched CSV is available:

```powershell
& "<python>" scripts/analyze_research_events.py --csv "<path-to-01_research_events_enriched_twelvedata.csv>" --out-dir "<analysis-output-dir>" --min-sample 10
```

Then inspect:

- `01_backtest_summary.md` for group-level evidence.
- `02_skill_candidates.md` for validated, weak, and failure patterns.
- `skill_candidate_patterns.csv` for machine-readable rule candidates.

## Reference Files

Load only what is needed:

- `references/event-schema.md`: field meanings and audit requirements.
- `references/validated-patterns.md`: current evidence-backed Serenity patterns.
- `references/failure-modes.md`: rules that prevent overfitting and narrative drift.
- `references/ticker-taxonomy.md`: symbol mapping, proxies, and coverage caveats.
- `references/ai-infrastructure-bottleneck-method.md`: how to identify AI infrastructure bottlenecks and underpriced beneficiaries.
- `references/cross-industry-bottleneck-framework.md`: how to generalize the bottleneck method to non-AI industries.
- `references/example-analysis.md`: expected output shape for future analyses.

## Output Standard

When asked to distill Serenity's investment thinking, produce:

1. Evidence-backed patterns, each with sample size and median excess return.
2. Weak hypotheses, explicitly labeled as such.
3. Failure modes and anti-rules.
4. A short research workflow that can be reused on new tweets or other industries.
5. Clear classification of early discovery vs continuation confirmation vs late/after-fact commentary.
6. Any proxy or data-quality caveats.

Never output a buy/sell recommendation. Output a research framework, signal audit, or skill rule draft.
