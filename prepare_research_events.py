#!/usr/bin/env python3
"""Build a falsifiable research event database from tweet scraper output."""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


UTC = ZoneInfo("UTC")
NY = ZoneInfo("America/New_York")

BULLISH_TERMS = {
    "bullish",
    "long",
    "favorite",
    "winner",
    "undervalued",
    "upside",
    "buy",
    "hold",
    "holding",
    "accumulate",
    "compounder",
    "breakout",
    "leader",
    "strong",
    "best",
    "great",
    "massive",
    "dominant",
    "leapfrog",
    "bottleneck",
    "scarce",
    "shortage",
    "rerate",
    "alpha",
}
BEARISH_TERMS = {
    "bearish",
    "short",
    "overvalued",
    "risk",
    "downside",
    "avoid",
    "bubble",
    "fraud",
    "weak",
    "bad",
    "concern",
    "problem",
    "broken",
    "selloff",
    "correction",
    "collapse",
    "dead",
    "wrong",
    "expensive",
}
EXIT_TERMS = {"sell", "sold", "exit", "trim", "trimmed", "take profit", "stop loss", "cut"}
WATCH_TERMS = {"watch", "watchlist", "radar", "tracking", "monitor", "looking at"}
UPDATE_TERMS = {"update", "today", "now", "again", "still", "reported", "earnings", "new", "continues"}

EVIDENCE_KEYWORDS = {
    "customer": {
        "customer",
        "customers",
        "client",
        "clients",
        "hyperscaler",
        "microsoft",
        "meta",
        "google",
        "amazon",
        "apple",
        "nvidia",
    },
    "supply_chain": {
        "supply",
        "capacity",
        "bottleneck",
        "shipment",
        "shipments",
        "fab",
        "foundry",
        "substrate",
        "cpo",
        "optics",
        "photonics",
        "hbm",
        "wafer",
        "inventory",
    },
    "earnings": {
        "earnings",
        "revenue",
        "margin",
        "guidance",
        "eps",
        "quarter",
        "q1",
        "q2",
        "q3",
        "q4",
        "backlog",
        "orders",
    },
    "valuation": {
        "valuation",
        "multiple",
        "ev/sales",
        "pe",
        "p/e",
        "market cap",
        "cheap",
        "expensive",
        "undervalued",
    },
    "technical": {
        "breakout",
        "chart",
        "support",
        "resistance",
        "vwap",
        "volume",
        "moving average",
        "gap",
        "squeeze",
    },
    "policy": {"tariff", "policy", "ban", "export", "china", "government", "regulation", "subsidy"},
    "rumor": {"rumor", "rumour", "heard", "unconfirmed", "maybe", "likely", "i think", "could", "seems"},
    "positioning": {"institution", "fund", "short interest", "float", "retail", "ownership"},
    "macro": {"rates", "fed", "inflation", "macro", "dollar", "recession", "liquidity", "market correction"},
}

HORIZON_KEYWORDS = [
    ("days", {"day", "days", "daily", "tomorrow", "overnight"}),
    ("weeks", {"week", "weeks", "weekly"}),
    ("months", {"month", "months", "quarter", "quarters", "q1", "q2", "q3", "q4", "2026"}),
    ("years", {"year", "years", "2027", "2028", "2030", "cycle", "multi-year"}),
]


def parse_json_stream(raw: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    pos = 0
    records: list[dict[str, Any]] = []
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        if pos >= len(raw):
            break
        obj, pos = decoder.raw_decode(raw, pos)
        records.append(obj)
    return records


def load_records(zip_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        records = parse_json_stream(archive.read("tweets.jsonl").decode("utf-8"))
        summary = json.loads(archive.read("summary.json").decode("utf-8"))
    return records, summary


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def market_session(dt: datetime | None) -> str:
    if dt is None:
        return "unknown"
    local = dt.astimezone(NY)
    if local.weekday() >= 5:
        return "weekend"
    current = local.time()
    if current < time(4, 0):
        return "overnight"
    if current < time(9, 30):
        return "premarket"
    if current < time(16, 0):
        return "intraday"
    if current < time(20, 0):
        return "after-hours"
    return "overnight"


def normalize_ticker(value: str) -> str:
    return value.upper().strip().lstrip("$").rstrip(".,;:!?)]}")


def record_tickers(record: dict[str, Any]) -> list[str]:
    tickers: list[str] = []
    for value in record.get("cashtags") or []:
        if isinstance(value, str):
            ticker = normalize_ticker(value)
            if ticker:
                tickers.append(ticker)
    text = str(record.get("rawContent") or "")
    for match in re.findall(r"\$[A-Za-z][A-Za-z0-9._-]{0,15}", text):
        ticker = normalize_ticker(match)
        if ticker:
            tickers.append(ticker)
    return sorted(set(tickers))


def tweet_text(record: dict[str, Any]) -> str:
    return str(record.get("rawContent") or record.get("content") or "").strip()


def tweet_url(record: dict[str, Any]) -> str:
    if record.get("url"):
        return str(record["url"])
    user = record.get("user") if isinstance(record.get("user"), dict) else {}
    username = user.get("username") or record.get("_requested_handle") or "i"
    tweet_id = record.get("id") or record.get("id_str")
    return f"https://x.com/{username}/status/{tweet_id}" if tweet_id else ""


def contains_term(text: str, term: str) -> bool:
    if " " in term or "/" in term:
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def contains_any(text: str, terms: set[str]) -> bool:
    return any(contains_term(text, term) for term in terms)


def classify_claim(text: str) -> str:
    lower = text.lower()
    if contains_any(lower, EXIT_TERMS):
        return "exit_hint"
    if contains_any(lower, BEARISH_TERMS) and not contains_any(lower, BULLISH_TERMS):
        return "bearish_risk"
    if contains_any(lower, BULLISH_TERMS):
        return "bullish_thesis"
    if contains_any(lower, WATCH_TERMS):
        return "watchlist"
    if contains_any(lower, UPDATE_TERMS):
        return "update"
    return "mention"


def evidence_types(text: str) -> str:
    lower = text.lower()
    hits = [label for label, terms in EVIDENCE_KEYWORDS.items() if contains_any(lower, terms)]
    return ";".join(hits) if hits else "unclear"


def time_horizon(text: str) -> str:
    lower = text.lower()
    hits = [label for label, terms in HORIZON_KEYWORDS if contains_any(lower, terms)]
    order = ["days", "weeks", "months", "years"]
    return ";".join(label for label in order if label in hits) if hits else "unclear"


def conviction_level(text: str, claim_type: str, engagement_score: int) -> int:
    lower = text.lower()
    score = 1
    if claim_type in {"bullish_thesis", "bearish_risk", "exit_hint"}:
        score += 1
    if len(text) > 700:
        score += 1
    if any(term in lower for term in ["favorite", "highest conviction", "strong conviction", "massive", "must own", "best"]):
        score += 1
    if engagement_score >= 10000:
        score += 1
    return max(1, min(5, score))


def engagement(record: dict[str, Any]) -> int:
    def metric(key: str) -> int:
        value = record.get(key)
        return int(value) if isinstance(value, (int, float)) else 0

    return metric("likeCount") + 2 * metric("retweetCount") + 3 * metric("quoteCount") + 2 * metric("replyCount")


def industry_node(ticker: str, text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["cpo", "optics", "photonics", "transceiver", "aaoi", "lite", "cohr"]):
        return "ai_networking_optics"
    if any(term in lower for term in ["hbm", "memory", "dram", "nand", "micron"]):
        return "memory_hbm_storage"
    if any(term in lower for term in ["foundry", "fab", "wafer", "substrate", "tsm", "tsem"]):
        return "semiconductor_manufacturing"
    if any(term in lower for term in ["gpu", "cuda", "accelerator", "nvda", "amd"]):
        return "ai_compute"
    if any(term in lower for term in ["power", "energy", "data center", "datacenter"]):
        return "ai_infrastructure_power"
    if any(term in lower for term in ["reddit", "social", "ads", "meta", "google"]):
        return "internet_platforms"
    return "unclear"


def ticker_positions(text: str, ticker: str) -> list[int]:
    pattern = re.compile(rf"\${re.escape(ticker)}(?![A-Za-z0-9._-])", re.IGNORECASE)
    return [match.start() for match in pattern.finditer(text)]


def target_role(ticker: str, text: str, tickers: list[str]) -> str:
    positions = ticker_positions(text, ticker)
    first = min(positions) if positions else 10_000
    count = len(positions)
    lower = text.lower()
    token = f"${ticker.lower()}"
    if count >= 2 or first <= 100:
        return "focal"
    if any(phrase in lower for phrase in [f"long {token}", f"short {token}", f"{token} is my", f"{token} looks", f"{token} could"]):
        return "focal"
    if any(word in lower for word in ["customer", "hyperscaler", "supplier", "supply", "powers", "maps to"]):
        return "supply_chain_context"
    if any(word in lower for word in ["versus", "vs", "peer", "competitor", "like", "basket"]):
        return "comparison_context"
    if len(tickers) >= 6:
        return "context"
    return "secondary"


def is_research_signal(role: str, claim_type: str, conviction: int) -> str:
    if role == "focal":
        return "yes"
    if role == "secondary" and claim_type in {"bullish_thesis", "bearish_risk", "exit_hint", "watchlist"} and conviction >= 3:
        return "maybe"
    return "no"


def text_excerpt(text: str, limit: int = 600) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "..."


def event_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        tickers = record_tickers(record)
        if not tickers:
            continue
        text = tweet_text(record)
        dt = parse_dt(record.get("date"))
        score = engagement(record)
        claim = classify_claim(text)
        conviction = conviction_level(text, claim, score)
        user = record.get("user") if isinstance(record.get("user"), dict) else {}
        for ticker in tickers:
            role = target_role(ticker, text, tickers)
            rows.append(
                {
                    "event_id": f"{record.get('id_str') or record.get('id')}:{ticker}",
                    "source_url": tweet_url(record),
                    "author": user.get("username") or record.get("_requested_handle") or "",
                    "published_at_utc": dt.astimezone(UTC).isoformat() if dt else str(record.get("date") or ""),
                    "published_at_et": dt.astimezone(NY).isoformat() if dt else "",
                    "market_session": market_session(dt),
                    "ticker": ticker,
                    "company": "",
                    "target_role": role,
                    "research_signal": is_research_signal(role, claim, conviction),
                    "industry_node": industry_node(ticker, text),
                    "claim_type": claim,
                    "conviction_level": conviction,
                    "evidence_type": evidence_types(text),
                    "time_horizon": time_horizon(text),
                    "entry_reference_price": "",
                    "entry_price_source": "",
                    "forward_return_1d": "",
                    "forward_return_5d": "",
                    "forward_return_20d": "",
                    "forward_return_60d": "",
                    "forward_return_120d": "",
                    "max_drawdown_after_signal": "",
                    "max_runup_after_signal": "",
                    "benchmark_return_20d": "",
                    "excess_return_20d": "",
                    "invalidation_condition": "",
                    "exit_condition": "",
                    "followup_posts": "",
                    "outcome_label": "",
                    "needs_human_review": "yes" if conviction >= 4 or claim in {"exit_hint", "bearish_risk"} else "no",
                    "engagement_score": score,
                    "like_count": record.get("likeCount") or 0,
                    "retweet_count": record.get("retweetCount") or 0,
                    "quote_count": record.get("quoteCount") or 0,
                    "reply_count": record.get("replyCount") or 0,
                    "view_count": record.get("viewCount") or 0,
                    "tweet_excerpt": text_excerpt(text),
                    "raw_text": re.sub(r"\s+", " ", text).strip(),
                    "notes": "",
                }
            )
    return sorted(rows, key=lambda row: (row["published_at_utc"], row["ticker"]))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_schema(path: Path) -> None:
    path.write_text(
        """# Research Event Schema

Each row is one ticker-level public research expression extracted from one tweet.

Directly generated fields:
- source_url
- author
- published_at_utc
- published_at_et
- market_session
- ticker
- target_role
- research_signal
- industry_node
- claim_type
- conviction_level
- evidence_type
- time_horizon
- engagement_score
- tweet_excerpt
- raw_text

Market-data fields to enrich:
- entry_reference_price
- forward_return_1d / 5d / 20d / 60d / 120d
- max_drawdown_after_signal
- max_runup_after_signal
- benchmark_return_20d
- excess_return_20d

The classification fields are heuristic labels, not investment conclusions.
Use research_signal=yes first; review maybe rows manually; avoid using no rows as direct signals.
""",
        encoding="utf-8",
    )


def write_review_queue(path: Path, rows: list[dict[str, Any]]) -> None:
    candidates = sorted(
        [row for row in rows if row["needs_human_review"] == "yes"],
        key=lambda row: (int(row["conviction_level"]), int(row["engagement_score"])),
        reverse=True,
    )[:120]
    lines = [
        "# Human Review Queue",
        "",
        "Review high-conviction, high-engagement, bearish, and exit-like events first.",
        "",
    ]
    for row in candidates:
        lines.append(f"## {row['published_at_et']} | ${row['ticker']} | {row['claim_type']} | conviction={row['conviction_level']}")
        lines.append("")
        lines.append(f"- URL: {row['source_url']}")
        lines.append(f"- Session: {row['market_session']}")
        lines.append(f"- Evidence: {row['evidence_type']}")
        lines.append(f"- Horizon: {row['time_horizon']}")
        lines.append(f"- Engagement: {row['engagement_score']}")
        lines.append("")
        lines.append(row["tweet_excerpt"])
        lines.append("")
        lines.append("Review fields:")
        lines.append("- claim_type:")
        lines.append("- conviction_level:")
        lines.append("- evidence_type:")
        lines.append("- time_horizon:")
        lines.append("- invalidation_condition:")
        lines.append("- exit_condition:")
        lines.append("- notes:")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_gap_report(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    by_claim = Counter(row["claim_type"] for row in rows)
    by_session = Counter(row["market_session"] for row in rows)
    by_ticker = Counter(row["ticker"] for row in rows)
    by_role = Counter(row["target_role"] for row in rows)
    by_signal = Counter(row["research_signal"] for row in rows)
    review_count = sum(1 for row in rows if row["needs_human_review"] == "yes")
    text = f"""# Research Event Gap Report

## Current Coverage

- Source handles: {', '.join(summary.get('handles', []))}
- Tweet count: {summary.get('tweet_count')}
- Event count: {len(rows)}
- Unique tickers: {len(by_ticker)}
- Human review candidates: {review_count}

## Claim Type Counts

{chr(10).join(f'- {key}: {value}' for key, value in by_claim.most_common())}

## Market Session Counts

{chr(10).join(f'- {key}: {value}' for key, value in by_session.most_common())}

## Target Role Counts

{chr(10).join(f'- {key}: {value}' for key, value in by_role.most_common())}

## Research Signal Counts

{chr(10).join(f'- {key}: {value}' for key, value in by_signal.most_common())}

## Top Tickers By Event Count

{chr(10).join(f'- ${key}: {value}' for key, value in by_ticker.most_common(40))}

## Missing For Backtest

These fields are intentionally blank until market data is attached:
- entry_reference_price
- forward_return_1d / 5d / 20d / 60d / 120d
- max_drawdown_after_signal
- max_runup_after_signal
- benchmark_return_20d
- excess_return_20d

These fields are heuristic and should be reviewed before final analysis:
- claim_type
- conviction_level
- evidence_type
- time_horizon
- invalidation_condition
- exit_condition
- outcome_label
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a falsifiable research event database from tweet scraper output.")
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out_dir or args.zip_path.parent / "research_events"
    out_dir.mkdir(parents=True, exist_ok=True)

    records, summary = load_records(args.zip_path)
    rows = event_rows(records)
    if not rows:
        raise RuntimeError("No ticker-level research events found.")

    write_schema(out_dir / "00_schema.md")
    write_csv(out_dir / "01_research_events.csv", rows)
    write_jsonl(out_dir / "01_research_events.jsonl", rows)
    write_review_queue(out_dir / "03_human_review_queue.md", rows)
    write_gap_report(out_dir / "04_gap_report.md", rows, summary)

    print(
        json.dumps(
            {
                "out_dir": str(out_dir),
                "event_count": len(rows),
                "unique_tickers": len({row["ticker"] for row in rows}),
                "human_review_candidates": sum(1 for row in rows if row["needs_human_review"] == "yes"),
                "files": sorted(path.name for path in out_dir.iterdir() if path.is_file()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
