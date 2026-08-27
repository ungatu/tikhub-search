# Platform recipes

TikHub changes tool catalogs and endpoint schemas. Inspect the connected MCP schemas first and use these recipes as current defaults, not immutable API definitions.

## Xiaohongshu / RED

Preferred MCP tool: `xiaohongshu_app_v2_search_notes`

First page:

```json
{
  "keyword": "用户的关键词",
  "page": 1,
  "sort_type": "general",
  "note_type": "不限",
  "time_filter": "不限",
  "search_id": "",
  "search_session_id": ""
}
```

For later pages, pass back both `search_id` and `search_session_id` returned by the prior search. Useful sorts include relevance, newest, most liked, most commented, and most collected; use the current schema's accepted values.

REST fallback: `GET /api/v1/xiaohongshu/app_v2/search_notes`

Optional comments: `xiaohongshu_app_v2_get_note_comments`. Prefer a validated `note_id` or share text and use returned pagination fields.

Official docs: <https://docs.tikhub.io/420136398e0>

## Douyin

Preferred MCP tool: `douyin_search_fetch_general_search_v2`. Fall back to V1 only when V2 is absent.

First page:

```json
{
  "keyword": "用户的关键词",
  "cursor": 0,
  "sort_type": "0",
  "publish_time": "0",
  "filter_duration": "0",
  "content_type": "0",
  "search_id": "",
  "backtrace": ""
}
```

For later pages, pass back `cursor`, `search_id`, and `backtrace`. Use the current tool schema/docs to translate latest, hot, time, duration, and content-type filters.

REST fallback: `POST /api/v1/douyin/search/fetch_general_search_v2`

Optional comments: `douyin_web_fetch_video_comments` with a validated `aweme_id`, returned cursor, and a bounded count.

Official docs catalog: <https://docs.tikhub.io/5448544m0>

## WeChat Official Accounts

Preferred MCP tool: `wechat_search_v2_fetch_search`.

Search Official Account articles, not Channels:

```json
{
  "keyword": "用户的关键词",
  "business_type": "article",
  "sort": "default",
  "publish_time": "all",
  "offset": 0,
  "raw": false
}
```

Supported vertical keys currently include `all`, `account`, `article`, `video`, `live_stream`, `moments`, `news`, `book`, `listen`, `image`, `encyclopedia`, and `weixin_index`.

- Use `article` for 微信公众号文章搜索.
- Use `account` only when the user asks to find a 公众号账号.
- Use `wechat_search_v2_fetch_search_videos` only for explicit 视频号 searches.

The `article` vertical can return zero for a query even when the same universal search contains Official Account articles. After a successful zero-result article response, make at most one bounded fallback call with the same query, sort, and time filter but `business_type="all"`, then filter the flattened `data.items`:

1. Keep items whose parsed `doc_url` host is exactly `mp.weixin.qq.com`.
2. If `doc_url` is missing, keep only items where `mpScene == 7` and `src_type == 49`.
3. Exclude items with `exportId`; those are Channels videos.
4. Do not keep ordinary web/news results merely because they have `doc_url`.

For `raw=false` article items, normalize these fields:

- `title`: strip the returned `<em class="highlight">` tags;
- `summary`: `desc`;
- `author`: `source.title`;
- `published_at`: numeric `timestamp` first, then `date` or `source.dateTime`;
- `url`: `doc_url`;
- `platform_id`: `docID`, preserved as a string.

TikHub documents `docID` and similar identifiers as 64-bit values. Never pass them through a JavaScript `Number`.

Current sort keys: `default`, `latest`, `hot`. Current publish-time keys: `all`, `day`, `week`, `half_year`.

For later pages, pass the returned `cursor` exactly. Increasing `offset` alone does not paginate and can return the first page again.

REST fallback: `POST /api/v1/wechat_search/v2/fetch_search`

Official endpoint and schema: <https://api.tikhub.io/api/v1/wechat_search/v2/fetch_search> and <https://api.tikhub.io/#/WeChat-Search-V2-API>.

Optional Official Account expansion:

- `wechat_mp_v2_fetch_article_detail`
- `wechat_mp_v2_fetch_article_stats`
- `wechat_mp_v2_fetch_article_comments`
- `wechat_mp_v2_fetch_comment_replies`
- `wechat_mp_v2_fetch_related_articles`
- `wechat_mp_v2_fetch_account_profile`
- `wechat_mp_v2_fetch_account_articles`

Official catalog: <https://docs.tikhub.io/472974860e0>

## Call and failure rules

- One query across all three platforms normally means three paid search calls.
- Run independent first-page searches concurrently when the client supports it.
- Retry only timeouts, `429`, and transient `5xx`, with bounded backoff. Do not repeatedly retry invalid parameters or an upstream error nested inside a successful envelope.
- Preserve each platform's own rank order unless the user explicitly requests another ordering.
- Report a partial result when one platform fails; do not hide the failure by returning only the successful platforms.
