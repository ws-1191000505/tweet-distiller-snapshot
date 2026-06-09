# Event Schema

Use this reference to interpret enriched research-event rows.

## Core Fields

- `source_url`: canonical tweet/post URL.
- `author`: source account.
- `published_at_utc`: event timestamp in UTC.
- `market_session`: premarket, intraday, after-hours, weekend, or unknown.
- `ticker`: extracted security symbol from the event.
- `company`: company name when known.
- `industry_node`: research taxonomy bucket.
- `claim_type`: mention, watchlist, bullish_thesis, bearish_risk, update, exit_hint, or other.
- `target_role`: focal ticker, context, customer, peer, supply-chain context, or comparison.
- `evidence_type`: customer, supply_chain, earnings, valuation, technical, policy, rumor, positioning, macro, or combinations.
- `time_horizon`: days, weeks, months, years, or unclear.
- `entry_reference_price`: price aligned to the event timestamp.
- `forward_return_*`: forward absolute returns.
- `benchmark_forward_return_*`: benchmark return over the same horizon.
- `excess_forward_return_*`: event return minus benchmark return.
- `max_drawdown_after_signal`: worst drawdown after event over measured window.
- `max_runup_after_signal`: best runup after event over measured window.
- `price_data_symbol`: symbol actually used for market data, including proxies.
- `price_data_status`: ok or missing status.

## Audit Rules

- Do not use rows without `source_url` and `published_at_utc` for skill rules.
- Treat `price_data_status != ok` as missing evidence.
- Use `price_data_symbol` for price interpretation when it differs from `ticker`.
- Cluster duplicate rows from the same tweet/thread before treating sample size as independent.
- Prefer benchmark-relative returns over absolute returns.
