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


DEFAULT_INSTRUMENTS = {
    # First US/ADR batch.
    "NVDA": {"symbol": "NVDA", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "NVIDIA Corporation"},
    "LITE": {"symbol": "LITE", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Lumentum Holdings"},
    "AAOI": {"symbol": "AAOI", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Applied Optoelectronics"},
    "AXTI": {"symbol": "AXTI", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "AXT Inc"},
    "MSFT": {"symbol": "MSFT", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Microsoft"},
    "INTC": {"symbol": "INTC", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Intel"},
    "AMZN": {"symbol": "AMZN", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Amazon"},
    "MRVL": {"symbol": "MRVL", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Marvell Technology"},
    "TSM": {"symbol": "TSM", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States", "currency": "USD", "name": "Taiwan Semiconductor ADR"},
    "AEHR": {"symbol": "AEHR", "exchange": "NASDAQ", "mic_code": "XNCM", "country": "United States", "currency": "USD", "name": "Aehr Test Systems"},
    "COHR": {"symbol": "COHR", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States", "currency": "USD", "name": "Coherent"},
    "AMD": {"symbol": "AMD", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Advanced Micro Devices"},
    "RDDT": {"symbol": "RDDT", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States", "currency": "USD", "name": "Reddit"},
    "POET": {"symbol": "POET", "exchange": "NASDAQ", "mic_code": "XNCM", "country": "United States", "currency": "USD", "name": "POET Technologies"},
    "GOOGL": {"symbol": "GOOGL", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Alphabet Class A"},
    "ARM": {"symbol": "ARM", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Arm Holdings ADR"},
    "AVGO": {"symbol": "AVGO", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Broadcom"},
    "SNDK": {"symbol": "SNDK", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Sandisk"},
    "JBL": {"symbol": "JBL", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States", "currency": "USD", "name": "Jabil"},
    # Added from Twelve Data /stocks discovery for high-frequency uncovered events.
    "SIVE": {"symbol": "SIVE", "exchange": "OMX", "mic_code": "XSTO", "country": "Sweden", "currency": "SEK", "name": "Sivers Semiconductors AB (publ)"},
    "SIVEF": {"symbol": "SIVEF", "exchange": "OTC", "mic_code": "PINX", "country": "United States", "currency": "USD", "name": "Sivers Semiconductors AB (publ) OTC"},
    "SOI": {"symbol": "SOI", "exchange": "Euronext", "mic_code": "XPAR", "country": "France", "currency": "EUR", "name": "Soitec SA"},
    "SLOIF": {"symbol": "SLOIF", "exchange": "OTC", "mic_code": "PINX", "country": "United States", "currency": "USD", "name": "Soitec SA OTC"},
    "RPI": {"symbol": "RPI", "exchange": "LSE", "mic_code": "XLON", "country": "United Kingdom", "currency": "GBp", "name": "Raspberry Pi Holdings plc"},
    "TSEM": {"symbol": "TSEM", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Tower Semiconductor"},
    "IQE": {"symbol": "IQE", "exchange": "LSE", "mic_code": "AIMX", "country": "United Kingdom", "currency": "GBp", "name": "IQE plc"},
    "IREN": {"symbol": "IREN", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "IREN Limited"},
    "NBIS": {"symbol": "NBIS", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Nebius Group"},
    "SMTOY": {"symbol": "SMTOY", "exchange": "OTC", "mic_code": "PINX", "country": "United States", "currency": "USD", "name": "Sumitomo Electric ADR"},
    "XFAB": {"symbol": "XFAB", "exchange": "Euronext", "mic_code": "XPAR", "country": "France", "currency": "EUR", "name": "X-FAB Silicon Foundries SE"},
    "META": {"symbol": "META", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Meta Platforms"},
    "TER": {"symbol": "TER", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Teradyne"},
    "MU": {"symbol": "MU", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Micron Technology"},
    "HOOD": {"symbol": "HOOD", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Robinhood Markets"},
    "IBKR": {"symbol": "IBKR", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Interactive Brokers"},
    "GFS": {"symbol": "GFS", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "GlobalFoundries"},
    "LPK": {"symbol": "LPK", "exchange": "XETR", "mic_code": "XETR", "country": "Germany", "currency": "EUR", "name": "LPKF Laser & Electronics SE"},
    "ALRIB": {"symbol": "ALRIB", "exchange": "Euronext", "mic_code": "XPAR", "country": "France", "currency": "EUR", "name": "Riber SA"},
    "HPS.A": {"symbol": "HPS.A", "exchange": "TSX", "mic_code": "XTSE", "country": "Canada", "currency": "CAD", "name": "Hammond Power Solutions"},
    "NVTS": {"symbol": "NVTS", "exchange": "NASDAQ", "mic_code": "XNMS", "country": "United States", "currency": "USD", "name": "Navitas Semiconductor"},
    "RKLB": {"symbol": "RKLB", "exchange": "NASDAQ", "mic_code": "XNCM", "country": "United States", "currency": "USD", "name": "Rocket Lab"},
    "FLNC": {"symbol": "FLNC", "exchange": "NASDAQ", "mic_code": "XNGS", "country": "United States", "currency": "USD", "name": "Fluence Energy"},
}

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
        default=",".join(DEFAULT_INSTRUMENTS),
        help="Comma-separated event tickers to enrich. Defaults to the validated US/ADR + international universe.",
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


def instrument_for_ticker(ticker: str) -> dict[str, str]:
    ticker = ticker.strip().upper().lstrip("$")
    if ticker in DEFAULT_INSTRUMENTS:
        return dict(DEFAULT_INSTRUMENTS[ticker])
    return {"symbol": ticker, "name": "", "exchange": "", "mic_code": "", "country": "", "currency": ""}


def cache_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)


def twelve_data_url(instrument: dict[str, str], start: date, end: date, api_key: str) -> str:
    params = {
        "symbol": instrument["symbol"],
        "interval": "1day",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "apikey": api_key,
        "format": "JSON",
        "outputsize": "5000",
    }
    for key in ["exchange", "mic_code", "country"]:
        if instrument.get(key):
            params[key] = instrument[key]
    return "https://api.twelvedata.com/time_series?" + urllib.parse.urlencode(params)


def fetch_bars(instrument: dict[str, str], start: date, end: date, api_key: str) -> tuple[list[Bar], str]:
    url = twelve_data_url(instrument, start, end, api_key)
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
    instruments_by_ticker: dict[str, dict[str, str]],
) -> dict[str, object]:
    enriched: dict[str, object] = dict(row)
    symbol = row.get("ticker", "").strip().upper().lstrip("$")
    event_time = parse_event_time(row.get("published_at_utc", "") or row.get("published_at", ""))
    bars = bars_by_symbol.get(symbol, [])
    instrument = instruments_by_ticker.get(symbol, instrument_for_ticker(symbol))

    for key in [
        "price_data_symbol",
        "price_data_name",
        "price_data_exchange",
        "price_data_mic_code",
        "price_data_country",
        "price_data_currency",
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
    enriched["price_data_symbol"] = instrument.get("symbol", symbol)
    enriched["price_data_name"] = instrument.get("name", "")
    enriched["price_data_exchange"] = instrument.get("exchange", "")
    enriched["price_data_mic_code"] = instrument.get("mic_code", "")
    enriched["price_data_country"] = instrument.get("country", "")
    enriched["price_data_currency"] = instrument.get("currency", "")
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
    instruments_by_ticker = {
        symbol: instrument_for_ticker(symbol)
        for symbol in selected_symbols
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

    symbols_to_fetch = sorted(selected_symbols)
    bars_by_symbol: dict[str, list[Bar]] = {}
    fetch_status: dict[str, str] = {}
    benchmark_instrument = instrument_for_ticker(args.benchmark.upper())
    fetch_plan = [(symbol, instruments_by_ticker[symbol]) for symbol in symbols_to_fetch]
    fetch_plan.append((args.benchmark.upper(), benchmark_instrument))
    for index, (event_ticker, instrument) in enumerate(fetch_plan, start=1):
        source = instrument.get("symbol", event_ticker)
        exchange = instrument.get("exchange", "")
        suffix = f" ({exchange})" if exchange else ""
        print(f"[{index}/{len(fetch_plan)}] Fetching {event_ticker} -> {source}{suffix} from {start} to {end}")
        bars, status = fetch_bars(instrument, start, end, api_key)
        bars_by_symbol[event_ticker] = bars
        fetch_status[event_ticker] = status
        cache_path = cache_dir / f"{cache_name(event_ticker)}.json"
        cache_path.write_text(
            json.dumps(
                {
                    "event_ticker": event_ticker,
                    "instrument": instrument,
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
        if index < len(fetch_plan) and args.sleep > 0:
            time.sleep(args.sleep)

    benchmark_bars = bars_by_symbol.get(args.benchmark.upper(), [])
    enriched_rows = [
        enrich_row(row, bars_by_symbol, benchmark_bars, instruments_by_ticker)
        for row in events
        if row.get("ticker", "").strip().upper().lstrip("$") in selected_symbols
        and row.get("research_signal", "").strip().lower() in {"yes", "maybe"}
    ]

    original_fields = list(events[0].keys()) if events else []
    extra_fields = [
        "price_data_symbol",
        "price_data_name",
        "price_data_exchange",
        "price_data_mic_code",
        "price_data_country",
        "price_data_currency",
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
        "selected_instruments": {
            symbol: instruments_by_ticker[symbol]
            for symbol in sorted(instruments_by_ticker)
        },
        "benchmark": args.benchmark.upper(),
        "benchmark_instrument": benchmark_instrument,
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
