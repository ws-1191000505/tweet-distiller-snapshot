# Validated Patterns

Current evidence comes from `enriched-research-events/research_events/analysis` generated with minimum sample size 10.

Treat these as research patterns, not trade recommendations.

## Strong Ticker-Level Patterns

These performed well in the current dataset, but must be interpreted through narrative context and prior-runup checks:

| Pattern | Evidence |
| --- | --- |
| `ticker=SIVE` priced via `SIVEF` | 67 priced events, median 20d excess return about +114.84%, excess win rate 100%, median drawdown about -13.77%. Use as a case study in small-cap bottleneck discovery, not as a generic ticker rule. |
| `ticker=AEHR` | 14 priced events, median 20d excess return about +88.05%, excess win rate about 92.86%. |
| `ticker=INTC` | 18 priced events, median 20d excess return about +47.57%, excess win rate about 94.12%. |
| `ticker=AMD` | 12 priced events, median 20d excess return about +32.33%, excess win rate 100%. |
| `ticker=SNDK` | 10 priced events, median 20d excess return about +25.37%, excess win rate 100%. |
| `ticker=MRVL` | 17 priced events, median 20d excess return about +10.01%, excess win rate about 78.57%. |

## Strong Evidence-Combination Pattern

`evidence_type=customer;supply_chain;earnings;rumor`

- 38 priced events.
- Median 20d excess return about +32.33%.
- Excess win rate about 70.97%.
- This is one of the best candidates for a reusable Serenity-style rule: prioritize claims where a customer link, supply-chain bottleneck, earnings/order evidence, and rumor/field-check signal reinforce one another.

## Manually Reviewed Case: SIVE

Manual review of the SIVE/SIVEF chart found that the 2026-03-27 event had meaningful prior runup before the tweet, but the subsequent move remained very large. Related SIVE events on 2026-03-29, 2026-03-31, and 2026-04-07 were also checked and found consistent with the thesis.

Interpret this cluster as `valid_continuation_confirmation`, not as a clean early-bottom discovery. The reusable pattern is:

1. A theme has already started to move.
2. The author adds concrete supply-chain, customer, funding, or capacity evidence.
3. The thesis continues to work after the confirmation despite prior momentum.

When using this as a skill example, describe the behavior as "continued confirmation of an already-moving thesis" rather than "buying the bottom."

## Interpreting The Pattern

The strongest reusable logic is not "buy every mentioned AI/semi stock." It is:

1. Identify a concrete AI infrastructure demand driver.
2. Map demand to a constrained layer: optical networking, InP, HBM, foundry, testing, substrate, thermal, or power.
3. Find a smaller or less-covered beneficiary whose capacity, customer exposure, or technical position is non-obvious.
4. Check whether the tweet is early relative to the price move.
5. Validate with forward excess returns and drawdown, not absolute returns.

## Rules That Can Enter A Skill

- Prioritize cross-evidence events over generic bullish language.
- Prefer focal ticker events over context tickers.
- Require price-path audit before treating a narrative as learned method.
- Preserve proxy labels, especially `SIVE -> SIVEF`.
- Convert strong examples into "how to search for bottlenecks" rather than "which ticker to buy."
