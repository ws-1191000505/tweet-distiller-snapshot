import argparse
import asyncio
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from twscrape import API, gather
from twscrape.logger import set_log_level


def parse_handles(value: str) -> list[str]:
    parts = re.split(r"[\s,]+", value.strip())
    handles = []
    seen = set()

    for part in parts:
        handle = part.strip().lstrip("@")
        if not handle:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
            raise ValueError(f"Invalid X/Twitter handle: {part}")
        key = handle.lower()
        if key not in seen:
            seen.add(key)
            handles.append(handle)

    if not handles:
        raise ValueError("At least one handle is required.")

    return handles


def model_to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "json"):
        return json.loads(obj.json())
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, dict):
        return obj
    raise TypeError(f"Unsupported model type: {type(obj)!r}")


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def tweet_url(tweet: dict[str, Any], fallback_handle: str) -> str:
    url = tweet.get("url")
    if url:
        return str(url)

    tweet_id = tweet.get("id") or tweet.get("id_str")
    username = get_nested(tweet, "user", "username", default=fallback_handle)
    return f"https://x.com/{username}/status/{tweet_id}" if tweet_id else ""


def slim_row(tweet: dict[str, Any], requested_handle: str) -> dict[str, Any]:
    return {
        "requested_handle": requested_handle,
        "tweet_id": tweet.get("id") or tweet.get("id_str"),
        "date": tweet.get("date"),
        "username": get_nested(tweet, "user", "username", default=requested_handle),
        "displayname": get_nested(tweet, "user", "displayname", default=""),
        "raw_content": tweet.get("rawContent") or tweet.get("content") or "",
        "lang": tweet.get("lang") or "",
        "reply_count": tweet.get("replyCount"),
        "retweet_count": tweet.get("retweetCount"),
        "like_count": tweet.get("likeCount"),
        "quote_count": tweet.get("quoteCount"),
        "view_count": tweet.get("viewCount"),
        "in_reply_to_tweet_id": tweet.get("inReplyToTweetId") or "",
        "retweeted_tweet_id": get_nested(tweet, "retweetedTweet", "id", default=""),
        "quoted_tweet_id": get_nested(tweet, "quotedTweet", "id", default=""),
        "url": tweet_url(tweet, requested_handle),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "requested_handle",
        "tweet_id",
        "date",
        "username",
        "displayname",
        "raw_content",
        "lang",
        "reply_count",
        "retweet_count",
        "like_count",
        "quote_count",
        "view_count",
        "in_reply_to_tweet_id",
        "retweeted_tweet_id",
        "quoted_tweet_id",
        "url",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_corpus(path: Path, rows: list[dict[str, Any]]) -> None:
    by_handle: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_handle.setdefault(str(row["requested_handle"]), []).append(row)

    lines = ["# Tweet Corpus", ""]
    for handle, handle_rows in by_handle.items():
        lines.extend([f"## @{handle}", ""])
        for row in sorted(handle_rows, key=lambda item: str(item.get("date") or "")):
            content = str(row.get("raw_content") or "").replace("\r", " ").strip()
            if not content:
                continue
            metrics = (
                f"replies={row.get('reply_count')}, "
                f"retweets={row.get('retweet_count')}, "
                f"likes={row.get('like_count')}, "
                f"quotes={row.get('quote_count')}"
            )
            lines.append(f"- {row.get('date')} | {metrics} | {row.get('url')}")
            lines.append(f"  {content}")
            lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_profile_prompt(path: Path, handles: list[str]) -> None:
    handle_text = ", ".join(f"@{handle}" for handle in handles)
    prompt = f"""# Distillation Prompt

你将基于 `corpus.md` 和 `tweets.csv` 分析这些 X/Twitter 发布者：{handle_text}。

请只基于给定推文，不要编造未出现过的事实。输出以下内容：

1. 核心主题：按重要性列出长期关注的主题，并给出代表性推文证据。
2. 观点结构：总结其反复出现的判断标准、价值偏好、因果模型和反对对象。
3. 写作风格：分析句式、语气、幽默感、术语、隐喻、节奏和互动方式。
4. 决策画像：推断其如何筛选信息、如何形成判断、如何表达不确定性。
5. 可复用表达模式：提取 10-20 条可迁移的表达模板。
6. 蒸馏注意事项：列出不能模仿或不应过度推断的部分。
7. 最终摘要：用 300-500 字给出一个紧凑的人格/观点/风格画像。

请把引用证据写成 `日期 + 推文 URL + 简短摘录` 的形式。
"""
    path.write_text(prompt, encoding="utf-8")


async def prepare_api(db_path: Path) -> API:
    cookies = os.getenv("TWS_COOKIES", "").strip()
    if not cookies:
        raise RuntimeError("Missing TWS_COOKIES. Add it as a GitHub Actions repository secret.")

    username = os.getenv("TWS_USERNAME", "x_account").strip() or "x_account"
    proxy = os.getenv("TWS_PROXY", "").strip() or None

    api = API(str(db_path), proxy=proxy)
    await api.pool.add_account(
        username=username,
        password="unused",
        email=f"{username}@example.invalid",
        email_password="unused",
        cookies=cookies,
    )
    await api.pool.login_all()
    return api


async def scrape_handle(api: API, handle: str, limit: int, include_replies: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    user = await api.user_by_login(handle)
    if user is None:
        raise RuntimeError(f"User not found or not visible: @{handle}")

    user_dict = model_to_dict(user)
    user_id = user_dict["id"]

    iterator = api.user_tweets_and_replies(user_id, limit=limit) if include_replies else api.user_tweets(user_id, limit=limit)
    tweets = await gather(iterator)

    records = []
    for tweet in tweets:
        data = model_to_dict(tweet)
        data["_requested_handle"] = handle
        records.append(data)

    return records, user_dict


async def run(args: argparse.Namespace) -> int:
    set_log_level(args.log_level)
    handles = parse_handles(args.handles)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    state_dir = Path(".twscrape-state")
    state_dir.mkdir(parents=True, exist_ok=True)
    api = await prepare_api(state_dir / "accounts.db")
    started_at = datetime.now(timezone.utc).isoformat()
    all_records: list[dict[str, Any]] = []
    users: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for handle in handles:
        try:
            records, user = await scrape_handle(api, handle, args.limit, args.include_replies)
            all_records.extend(records)
            users[handle] = user
            print(f"@{handle}: collected {len(records)} tweets")
        except Exception as exc:
            errors[handle] = f"{type(exc).__name__}: {exc}"
            print(f"@{handle}: failed: {errors[handle]}")

    rows = [slim_row(record, str(record.get("_requested_handle") or "")) for record in all_records]

    write_jsonl(out_dir / "tweets.jsonl", all_records)
    write_csv(out_dir / "tweets.csv", rows)
    write_corpus(out_dir / "corpus.md", rows)
    write_profile_prompt(out_dir / "profile_prompt.md", handles)

    summary = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "handles": handles,
        "limit_per_handle": args.limit,
        "include_replies": args.include_replies,
        "tweet_count": len(all_records),
        "user_count": len(users),
        "users": users,
        "errors": errors,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors and not all_records:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a one-off X/Twitter tweet snapshot for distillation.")
    parser.add_argument("--handles", required=True, help="Comma/newline/space separated handles, without or with @.")
    parser.add_argument("--limit", type=int, default=3200, help="Maximum tweets per handle.")
    parser.add_argument("--include-replies", action="store_true", help="Use user_tweets_and_replies instead of user_tweets.")
    parser.add_argument("--output-dir", default="out", help="Directory for exported files.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be greater than zero.")

    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
