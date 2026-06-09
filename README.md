# Tweet Distiller Snapshot

Tweet Distiller Snapshot is an end-to-end public research pipeline for turning an X/Twitter author's public posts into a falsifiable investment research dataset and, finally, a reusable Codex skill.

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

## Repository Contents

```text
.github/workflows/
  scrape.yml                    # GitHub Actions workflow for X/Twitter snapshot scraping
  enrich-research-events.yml     # Workflow for research-event preparation and market-data enrichment

scrape.py                        # One-time X/Twitter snapshot scraper using twscrape
prepare_distill_pack.py          # Builds corpus, prompt, topic candidates, and evidence index
prepare_research_events.py       # Converts posts into structured investment research events
enrich_research_events_twelvedata.py
                                 # Adds prices, forward returns, drawdown, runup, benchmark returns
analyze_research_events.py       # Builds grouped backtest summaries and skill candidates
make_manual_review_queue.py      # Creates a manual chart-review queue

skills/serenity-research-analyst/ # Codex skill distilled from the research process
docs/                            # Project-level explanation and publication notes
```

## Main Outputs

Important generated artifacts live under `enriched-research-events/research_events/`.

Key outputs include:

- `enriched/01_research_events_enriched_twelvedata.csv`: event-level dataset with market enrichment.
- `analysis/01_backtest_summary.md`: group-level performance summary.
- `analysis/02_skill_candidates.md`: candidate rules, weak patterns, and contra-signals.
- `analysis/03_manual_review_v1.md`: human chart-review queue.
- `analysis/manual_review_labels.csv`: manual review labels.
- `analysis/04_serenity_bottleneck_methodology.md`: AI infrastructure bottleneck methodology.
- `analysis/05_skill_trial_ai_infra_map_v1.md`: skill trial output.
- `analysis/06_skill_trial_cross_industry_power_grid.md`: cross-industry generalization test.
- `analysis/07_skill_trial_report.md`: skill trial report.

## Result Snapshot

In the current enriched Serenity dataset:

- 2,026 structured research events were created from public tweets.
- 600 rows were enriched in the latest public artifact.
- 554 rows had usable price data.
- SIVE was priced through the free-data proxy `SIVEF`.
- The strongest reusable evidence pattern was `customer;supply_chain;earnings;rumor`.

Selected findings:

| Pattern | Evidence |
| --- | --- |
| `SIVE` / `SIVEF` | Strong forward performance, manually reviewed as continuation confirmation rather than early-bottom discovery. |
| `AEHR` | Strong cluster, but requires duplicate/thread clustering before treating sample size as independent. |
| `customer;supply_chain;earnings;rumor` | Strongest reusable evidence-stack pattern in the dataset. |
| Broad `ai_networking_optics` | Weak as a broad theme despite strong sub-bottlenecks; this prevents naive theme-following. |
| Large-cap/context names | Often useful as demand validation, not direct alpha signals. |

## The Codex Skill

The distilled skill is in:

```text
skills/serenity-research-analyst/
```

It teaches Codex to:

- analyze timestamped investment research events;
- separate narrative logic, signal logic, and risk logic;
- identify AI infrastructure bottlenecks and underpriced beneficiaries;
- classify events as early discovery, continuation confirmation, late validation, after-fact commentary, or context-only;
- generalize the bottleneck method to other industries;
- avoid overfitting to tickers, broad themes, and duplicate tweet rows.

To install locally:

```powershell
Copy-Item -Recurse -Force `
  -LiteralPath ".\skills\serenity-research-analyst" `
  -Destination "$env:USERPROFILE\.codex\skills\serenity-research-analyst"
```

Restart Codex after installation if the skill list does not refresh automatically.

## GitHub Actions Usage

### 1. Scrape Public Tweets

Open `Actions -> Scrape X/Twitter snapshot -> Run workflow`.

Inputs:

| Input | Example | Notes |
| --- | --- | --- |
| `handles` | `aleabitoreddit` | X/Twitter handles without `@`. |
| `limit` | `3200` | X/Twitter/twscrape commonly caps user timelines around this level. |
| `include_replies` | `false` | Whether to include replies. |
| `original_only` | `true` | Exclude replies, reposts, and quote tweets where possible. |

Required secret:

| Secret | Required | Notes |
| --- | --- | --- |
| `TWS_COOKIES` | Yes | X/Twitter cookies, usually `auth_token=...; ct0=...`. |
| `TWS_USERNAME` | No | Account label for twscrape. |
| `TWS_PROXY` | No | Optional proxy. |

### 2. Build And Enrich Research Events

Open `Actions -> Enrich research events -> Run workflow`.

This workflow can prepare structured research events and enrich them with market data. The Twelve Data free tier has strict rate limits, so the workflow includes pacing controls. Use GitHub Secrets for API keys.

Common secrets:

| Secret | Required | Notes |
| --- | --- | --- |
| `TWELVEDATA_API_KEY` | For Twelve Data enrichment | Used for stock price enrichment. |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | Optional | Supported by older enrichment script if you have keys. |

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
