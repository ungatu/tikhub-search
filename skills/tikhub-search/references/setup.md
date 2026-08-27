# TikHub setup

## Connect the three required MCP servers

Create a TikHub account and API key at <https://user.tikhub.io>. Keep the key in the environment that launches Codex; never paste it into chat or commit it.

When creating the token, enable the scopes required by WeChat Search V2 and, when article expansion is needed, WeChat Media Platform V2. A token can be valid for user/account APIs while still returning `403` for WeChat calls when these scopes are missing.

```bash
codex mcp add tikhub-xiaohongshu \
  --url https://mcp.tikhub.io/xiaohongshu/mcp \
  --bearer-token-env-var TIKHUB_API_KEY

codex mcp add tikhub-douyin \
  --url https://mcp.tikhub.io/douyin/mcp \
  --bearer-token-env-var TIKHUB_API_KEY

codex mcp add tikhub-wechat \
  --url https://mcp.tikhub.io/wechat/mcp \
  --bearer-token-env-var TIKHUB_API_KEY
```

Verify with `codex mcp list`, then restart Codex or open a new task so the tools are discovered.

TikHub's WeChat server covers both Official Accounts and Channels. This skill uses Official Account article search by default and does not require a separate “公众号” server.

Official MCP sources:

- <https://mcp.tikhub.io/>
- <https://mcp.tikhub.io/platforms>

## REST fallback

The bundled client uses `TIKHUB_API_KEY` and performs a dry run unless `--execute` is present:

```bash
python3 scripts/tikhub_api.py GET /api/v1/tikhub/user/get_user_info
```

Example WeChat article-search payload:

```json
{
  "keyword": "人工智能",
  "business_type": "article",
  "sort": "latest",
  "publish_time": "week",
  "offset": 0,
  "raw": false
}
```

```bash
python3 scripts/tikhub_api.py \
  --execute \
  --data-file payload.json \
  --output data/wechat-search.json \
  POST /api/v1/wechat_search/v2/fetch_search
```

Check the current endpoint schema and price before executing a REST request. The current official OpenAPI documents this search at `https://api.tikhub.io/api/v1/wechat_search/v2/fetch_search`, priced at $0.01 per call, with a recommended timeout of at least 30 seconds. Use `TIKHUB_API_BASE_URL` only when an official TikHub notice specifies another base.

## Troubleshooting

- `401`: confirm the key is valid and visible to the Codex host process.
- `403`: inspect the safe error message for missing token scopes; enable WeChat Search V2/Media Platform V2 as required. Never print or persist returned `detail.headers`, because upstream errors may echo the Authorization header.
- Server missing: run `codex mcp list`, then restart or open a new task.
- No 公众号 results: first confirm `business_type="article"` and `raw=false`; if the successful response still has `data.count=0`, make one `all` fallback call and keep only `mp.weixin.qq.com` items (or the paired `mpScene=7` and `src_type=49` markers).
- Repeated first page on WeChat: paginate with the returned `cursor`; changing `offset` alone is ineffective.
- Timeout/`429`: reduce concurrency and retry with bounded backoff.
- Upstream error inside `code: 200`: treat it as a failed result, not an empty search.
