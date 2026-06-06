#!/usr/bin/env python3
"""Enrich tweet research events with daily price data from Twelve Data.

This script is designed for GitHub Actions. It reads the structured event CSV
created by prepare_research_events.py, fetches daily OHLCV bars for a small US
equity universe, and writes forward return / drawdown columns for falsifiable
investment research.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


DEFAULT_UNIVERSE = [
    "NVDA",
    "LITE",
    "AAOI",
    "AXTI",
    "MSFT",
    "INTC",
    "AMZN",
    "MRVL",
    "TSM",
    "AEHR",
    "COHR",
    "AMD",
    "RDDT",
    "POET",
    "GOOGL",
    "ARM",
    "AVGO",
    "SNDK",
    "JBL",
]

FORWARD_WINDOWS = [1, 5, 20, 60, 120]
NY = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Bar:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "events_csv",
        help="Path to research_events/01_research_events.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="research_events/enriched",
        help="Directory for enriched CSV, price cache, and report files.",
    )
    parser.add_argument(
        "--symbols",
        default=",".join(DEFAULT_UNIVERSE),
        help="Comma-separated symbols to enrich. Defaults to the first validated US/ADR universe.",
    )
    parser.add_argument(
        "--benchmark",
        default="SOXX",
        help="Benchmark ETF symbol used for benchmark-relative forward returns.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=8.0,
        help="Seconds to sleep between Twelve Data requests. Keep conservative for free plans.",
    )
    parser.add_argument(
        "--api-key-env",
        default="TWELVE_DATA_API_KEY",
        help="Environment variable containing the Twelve Data API key.",
    )
    return parser.parse_args()


def parse_event_time(value: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def twelve_data_url(symbol: str, start: date, end: date, api_key: str) -> str:
    params = {
        "symbol": symbol,
        "interval": "1day",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "apikey": api_key,
        "format": "JSON",
        "outputsize": "5000",
    }
    return "https://api.twelvedata.com/time_series?" + urllib.parse.urlencode(params)


def fetch_bars(symbol: str, start: date, end: date, api_key: str) -> tuple[list[Bar], str]:
    url = twelve_data_url(symbol, start, end, api_key)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "tweet-distiller-research-events/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - report network/API failures per symbol.
        return [], f"request_error:{type(exc).__name__}:{exc}"

    if not isinstance(payload, dict):
        return [], "bad_response:not_object"

    status = str(payload.get("status", "")).lower()
    if status == "error":
        message = str(payload.get("message", "unknown_error")).replace("\n", " ")
        return [], f"api_error:{message}"

    values = payload.get("values")
    if not isinstance(values, list) or not values:
        message = str(payload.get("message", "no_values")).replace("\n", " ")
        return [], f"no_values:{message}"

    bars: list[Bar] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        dt_raw = item.get("datetime")
        if not dt_raw:
            continue
        try:
            day = date.fromisoformat(str(dt_raw)[:10])
        except ValueError:
            continue
        open_ = parse_float(item.get("open"))
        high = parse_float(item.get("high"))
        low = parse_float(item.get("low"))
        close = parse_float(item.get("close"))
        if open_ is None or high is None or low is None or close is None:
            continue
        bars.append(
            Bar(
                day=day,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=parse_float(item.get("volume")),
            )
        )
    bars.sort(key=lambda bar: bar.day)
    return bars, "ok" if bars else "no_parseable_bars"


def load_events(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def first_bar_on_or_after(bars: list[Bar], target: date) -> int | None:
    for index, bar in enumerate(bars):
        if bar.day >= target:
            return index
    return None


def pct_return(start_price: float | None, end_price: float | None) -> float | None:
    if start_price is None or end_price is None or start_price == 0:
        return None
    return (end_price / start_price - 1.0) * 100.0


def max_runup(entry: float, bars: list[Bar]) -> float | None:
    if not bars or entry == 0:
        return None
    return (max(bar.high for bar in bars) / entry - 1.0) * 100.0


def max_drawdown(entry: float, bars: list[Bar]) -> float | None:
    if not bars or entry == 0:
        return None
    return (min(bar.low for bar in bars) / entry - 1.0) * 100.0


def round_or_blank(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def market_reference_day(event_time: datetime) -> date:
    # Tweets after the US cash close are evaluated from the next calendar day;
    # first_bar_on_or_after then lands on the next trading day.
    event_et = event_time.astimezone(NY)
    if event_et.time() >= datetime.strptime("16:00", "%H:%M").time():
        return event_et.date() + timedelta(days=1)
    return event_et.date()


def enrich_row(
    row: dict[str, str],
    bars_by_symbol: dict[str, list[Bar]],
    benchmark_bars: list[Bar],
) -> dict[str, object]:
    enriched: dict[str, object] = dict(row)
    symbol = row.get("ticker", "").strip().upper().lstrip("$")
    event_time = parse_event_time(row.get("published_at_utc", "") or row.get("published_at", ""))
    bars = bars_by_symbol.get(symbol, [])

    for key in [
        "price_data_symbol",
        "price_data_status",
        "entry_reference_date",
        "entry_reference_price",
        "benchmark_entry_price",
        "max_runup_after_signal_pct",
        "max_drawdown_after_signal_pct",
    ]:
        enriched.setdefault(key, "")
    for window in FORWARD_WINDOWS:
        enriched.setdefault(f"forward_return_{window}d_pct", "")
        enriched.setdefault(f"benchmark_forward_return_{window}d_pct", "")
        enriched.setdefault(f"excess_forward_return_{window}d_pct", "")

    if not event_time:
        enriched["price_data_status"] = "missing_event_time"
        return enriched
    if not bars:
        enriched["price_data_status"] = "missing_symbol_bars"
        return enriched

    reference_day = market_reference_day(event_time)
    entry_index = first_bar_on_or_after(bars, reference_day)
    if entry_index is None:
        enriched["price_data_status"] = "no_bar_on_or_after_event"
        return enriched

    entry_bar = bars[entry_index]
    entry_price = entry_bar.close
    enriched["price_data_symbol"] = symbol
    enriched["price_data_status"] = "ok"
    enriched["entry_reference_date"] = entry_bar.day.isoformat()
    enriched["entry_reference_price"] = round_or_blank(entry_price)

    benchmark_entry_index = first_bar_on_or_after(benchmark_bars, reference_day)
    benchmark_entry_price: float | None = None
    if benchmark_entry_index is not None and benchmark_bars:
        benchmark_entry_price = benchmark_bars[benchmark_entry_index].close
        enriched["benchmark_entry_price"] = round_or_blank(benchmark_entry_price)

    future_slice = bars[entry_index + 1 :]
    if future_slice:
        enriched["max_runup_after_signal_pct"] = round_or_blank(max_runup(entry_price, future_slice))
        enriched["max_drawdown_after_signal_pct"] = round_or_blank(max_drawdown(entry_price, future_slice))

    for window in FORWARD_WINDOWS:
        target_index = entry_index + window
        if target_index < len(bars):
            ret = pct_return(entry_price, bars[target_index].close)
            enriched[f"forward_return_{window}d_pct"] = round_or_blank(ret)
        else:
            ret = None

        benchmark_ret = None
        if (
            benchmark_entry_index is not None
            and benchmark_entry_price is not None
            and benchmark_entry_index + window < len(benchmark_bars)
        ):
            benchmark_ret = pct_return(
                benchmark_entry_price,
                benchmark_bars[benchmark_entry_index + window].close,
            )
            enriched[f"benchmark_forward_return_{window}d_pct"] = round_or_blank(benchmark_ret)

        if ret is not None and benchmark_ret is not None:
            enriched[f"excess_forward_return_{window}d_pct"] = round_or_blank(ret - benchmark_ret)

    return enriched


def main() -> int:
    args = parse_args()
    api_key = os.getenv(args.api_key_env, "").strip()
    if not api_key:
        print(f"Missing required environment variable: {args.api_key_env}", file=sys.stderr)
        return 2

    events_path = Path(args.events_csv)
    out_dir = Path(args.out_dir)
    events = load_events(events_path)

    selected_symbols = {
        symbol.strip().upper().lstrip("$")
        for symbol in args.symbols.split(",")
        if symbol.strip()
    }
    event_dates = [
        parse_event_time(row.get("published_at_utc", "") or row.get("published_at", ""))
        for row in events
        if row.get("ticker", "").strip().upper().lstrip("$") in selected_symbols
    ]
    event_dates = [dt for dt in event_dates if dt is not None]
    if not event_dates:
        print("No events matched the selected symbol universe.", file=sys.stderr)
        return 2

    start = min(dt.date() for dt in event_dates) - timedelta(days=10)
    end = date.today() + timedelta(days=1)

    cache_dir = out_dir / "price_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    symbols_to_fetch = sorted(selected_symbols | {args.benchmark.upper()})
    bars_by_symbol: dict[str, list[Bar]] = {}
    fetch_status: dict[str, str] = {}
    for index, symbol in enumerate(symbols_to_fetch, start=1):
        print(f"[{index}/{len(symbols_to_fetch)}] Fetching {symbol} from {start} to {end}")
        bars, status = fetch_bars(symbol, start, end, api_key)
        bars_by_symbol[symbol] = bars
        fetch_status[symbol] = status
        cache_path = cache_dir / f"{symbol}.json"
        cache_path.write_text(
            json.dumps(
                {
                    "symbol": symbol,
                    "status": status,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "bars": [bar.__dict__ | {"day": bar.day.isoformat()} for bar in bars],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if index < len(symbols_to_fetch) and args.sleep > 0:
            time.sleep(args.sleep)

    benchmark_bars = bars_by_symbol.get(args.benchmark.upper(), [])
    enriched_rows = [
        enrich_row(row, bars_by_symbol, benchmark_bars)
        for row in events
        if row.get("ticker", "").strip().upper().lstrip("$") in selected_symbols
        and row.get("research_signal", "").strip().lower() in {"yes", "maybe"}
    ]

    original_fields = list(events[0].keys()) if events else []
    extra_fields = [
        "price_data_symbol",
        "price_data_status",
        "entry_reference_date",
        "entry_reference_price",
        "benchmark_entry_price",
        "max_runup_after_signal_pct",
        "max_drawdown_after_signal_pct",
    ]
    for window in FORWARD_WINDOWS:
        extra_fields.extend(
            [
                f"forward_return_{window}d_pct",
                f"benchmark_forward_return_{window}d_pct",
                f"excess_forward_return_{window}d_pct",
            ]
        )
    fieldnames = original_fields + [field for field in extra_fields if field not in original_fields]
    write_csv(out_dir / "01_research_events_enriched_twelvedata.csv", enriched_rows, fieldnames)

    ok_rows = sum(1 for row in enriched_rows if row.get("price_data_status") == "ok")
    report = {
        "input_events_csv": str(events_path),
        "output_csv": str(out_dir / "01_research_events_enriched_twelvedata.csv"),
        "selected_symbols": sorted(selected_symbols),
        "benchmark": args.benchmark.upper(),
        "event_rows_written": len(enriched_rows),
        "rows_with_price_data": ok_rows,
        "price_start": start.isoformat(),
        "price_end": end.isoformat(),
        "fetch_status": fetch_status,
    }
    (out_dir / "00_enrichment_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
