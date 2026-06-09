# Failure Modes

Use this file to prevent overfitting Serenity-style research into a story engine.

## Anti-Rules From Current Data

- `claim_type=bullish_thesis` is not automatically alpha. In the current dataset it had negative median 20d excess return despite positive absolute returns.
- Broad `ai_networking_optics` exposure can underperform SOXX after the tweet timestamp. The theme may be correct while the trade is late.
- Do not reject or accept a thesis from broad industry nodes alone. A weak parent node can contain a strong sub-bottleneck, and a strong parent node can hide weak beneficiaries.
- Large-cap mentions such as NVDA, LITE, MSFT, TSM, and AMZN can show positive absolute forward returns but weak or negative SOXX-relative returns.
- `watchlist` and `mention` rows are often too weak to use as direct signals.
- Do not treat a customer or peer ticker as a signal when `target_role` is context, comparison_context, or supply_chain_context.
- Do not infer failure from `price_data_status != ok`; that means uncovered data, not negative performance.

## Data Problems To Flag

- Proxy symbols: `SIVE` is priced with `SIVEF` in the free-data workflow.
- Free Twelve Data coverage excludes some non-US primary listings.
- OTC instruments may have liquidity, stale-price, or spread issues. Treat large returns as research evidence needing manual inspection.
- Duplicate events from the same tweet/thread can inflate apparent sample size.
- Repeated rows from one source tweet or thread must be clustered before treating sample size as independent evidence.
- If `industry_node=unclear` performs well, treat it as a taxonomy gap requiring reclassification, not as a real investable category.
- Tweets posted after major moves may make the narrative true but late.
- Manual SIVE review showed a useful middle case: meaningful prior runup did not invalidate the signal, because later upside was still large. Label this as continuation confirmation, not early discovery.

## Manual Review Checklist

Before writing a skill rule:

1. Read the source tweets for the top examples.
2. Check whether the event is a first signal, a follow-up, or an after-the-fact update.
3. Check if multiple rows came from one tweet and should be clustered.
4. Check the prior 20 trading days for runup.
5. Compare absolute return with SOXX-relative excess return.
6. Identify an invalidation condition that would have broken the thesis.
7. If prior runup exists but later upside remains large, classify the event as continuation confirmation rather than rejecting it or treating it as an early signal.
8. For non-semiconductor industries, replace SOXX with an industry benchmark or peer basket.

## Language Discipline

Avoid phrases like "Serenity is good at X" unless backed by grouped statistics. Prefer "In this dataset, events matching X had Y sample size and Z median excess return."
