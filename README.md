# Tweet Distiller Snapshot

一次性抓取指定 X/Twitter 发布者截至当前可见推文，并导出为适合后续“人格/观点/写作风格蒸馏”的数据包。

这个项目按公开 GitHub 仓库设计：代码、说明、工作流都可以公开；运行用的 X/Twitter cookie 请放在 GitHub Secrets，不要写入仓库。

## 适用场景

- 单次抓取一个或多个账号的近期可见推文。
- 不在本机运行，使用 GitHub Actions 云端 runner。
- 输出 JSONL、CSV、Markdown 语料和蒸馏提示词模板。
- 结果作为 GitHub Actions artifact 下载。

## 现实限制

- 本项目使用 `twscrape`，它依赖已登录的 X/Twitter 账号 cookie。
- `twscrape` README 说明 `user_tweets` 和 `user_tweets_and_replies` 通常最多约 3200 条，实际数量取决于 X/Twitter 当前接口、账号状态和限流。
- X/Twitter 抓取存在不稳定性，请控制频率，并遵守平台条款和所在地法律法规。
- 公开仓库的 artifact 和运行日志应视为公开可见；如果结果不宜公开，请改用私有仓库或不要上传 artifact。

## 第一次配置

1. 新建一个公开 GitHub 仓库。
2. 上传本目录里的所有文件。
3. 打开仓库的 `Settings -> Secrets and variables -> Actions -> New repository secret`。
4. 添加以下 Secret：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `TWS_USERNAME` | 否 | twscrape 数据库里的账号标签，可填你的 X 用户名，也可填 `x_account` |
| `TWS_COOKIES` | 是 | 浏览器里的 X cookie，格式如 `auth_token=xxx; ct0=yyy` |
| `TWS_PROXY` | 否 | 如需代理，填 `http://user:pass@host:port` 或 `socks5://...` |

获取 cookie 的常见方式：

1. 在浏览器登录 `https://x.com`。
2. 打开开发者工具。
3. 找到 `Application / Storage -> Cookies -> https://x.com`。
4. 复制 `auth_token` 和 `ct0`，拼成：

```text
auth_token=你的值; ct0=你的值
```

## 手动运行

1. 打开 GitHub 仓库的 `Actions`。
2. 选择 `Scrape X/Twitter snapshot`。
3. 点击 `Run workflow`。
4. 填写：

| 输入项 | 示例 | 说明 |
| --- | --- | --- |
| `handles` | `sama,paulg` | 账号名，不需要 `@`，多个用逗号或换行分隔 |
| `limit` | `3200` | 每个账号最多尝试抓取多少条 |
| `include_replies` | `false` | 是否包含回复 |
| `original_only` | `true` | 是否只导出原创推文；开启后会排除回复、转推和引用推文 |

运行结束后，在 workflow run 页面下载 `tweet-distiller-snapshot` artifact。

## 输出文件

artifact 内部结构类似：

```text
out/
├─ tweets.jsonl
├─ tweets.csv
├─ corpus.md
├─ profile_prompt.md
└─ summary.json
```

- `tweets.jsonl`：完整结构化数据，一行一条。
- `tweets.csv`：常用字段表格，适合粗看和筛选。
- `corpus.md`：按账号整理的纯文本语料。
- `profile_prompt.md`：用于让大模型分析发布者风格、主题、观点和表达模式的提示词模板。
- `summary.json`：本次运行的账号、数量、时间和错误信息。

## 本地测试

如果要在本地小样本测试：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TWS_COOKIES='auth_token=xxx; ct0=yyy'
python scrape.py --handles sama --limit 20 --original-only
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:TWS_COOKIES='auth_token=xxx; ct0=yyy'
python scrape.py --handles sama --limit 20 --original-only
```
