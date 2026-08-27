---
name: tikhub-search
description: Search public content through TikHub on Xiaohongshu/RED, Douyin, and WeChat Official Accounts, then return a consistent result list with source links. Use when Codex needs walled-garden search, recent content discovery, demand or pain-point signals, public comment leads, creator/account lookup, or current technical discussions from 小红书、抖音、微信公众号、微信文章、TikHub. Also use to expand selected public results into details or comments when the user explicitly asks. Keep the workflow read-only; do not use it for private data, account actions, engagement automation, or generic open-web search that does not need TikHub.
---

# TikHub Search

Treat this skill as a thin search adapter, not a research methodology. Search the requested TikHub platforms, normalize the useful fields, and stop unless the user asks for analysis or deeper retrieval.

## Load references only when needed

- Read [setup.md](references/setup.md) when a required TikHub MCP server is missing or authentication fails.
- Read [platforms.md](references/platforms.md) before the first call to a platform, when choosing filters, or when pagination is requested.
- Read [output-format.md](references/output-format.md) when returning JSON/CSV, saving results, or combining platforms.

## Resolve the request

Extract these inputs from the user's words:

- `query`: required search text;
- `platforms`: any of `xiaohongshu`, `douyin`, `wechat`;
- `sort`: relevance by default, or latest/hot when requested;
- `time_range`: unrestricted unless requested;
- `limit`: one result page per platform by default;
- `expand`: none by default, or selected details/comments when requested.

If the user names platforms, use only those platforms. If the user asks for TikHub or Chinese social-platform search without naming platforms, search all three required platforms: Xiaohongshu, Douyin, and WeChat Official Accounts.

Interpret “微信/公众号搜索” as Official Account articles. Do not substitute WeChat Channels. Use Channels only when the user explicitly says “视频号”.

## Search

1. Prefer connected TikHub MCP tools. Inspect the current tool names and input schemas before calling because TikHub can change its catalog.
2. Prefer these currently supported tools when present:
   - Xiaohongshu: `xiaohongshu_app_v2_search_notes`
   - Douyin: `douyin_search_fetch_general_search_v2`
   - WeChat Official Accounts: `wechat_search_v2_fetch_search` with `business_type="article"` and `raw=false`
3. A direct user request to search authorizes one first-page call per requested platform. Do not interrupt a normal three-platform search with a budget questionnaire.
4. Before additional pages or bulk detail/comment calls, state the proposed number of extra calls. Proceed without another question only when the user already supplied a page, call, or spend limit that covers them.
5. Preserve the user's query. Add at most one obvious synonym or error-string variant only after a zero-result search or when the user asks for query expansion.
6. Follow returned cursors and session IDs exactly. Never synthesize pagination values.
7. Validate both transport status and TikHub's response envelope. Report upstream errors as errors, even when the outer response says `code: 200`.

For WeChat Official Account articles, treat the article vertical as the primary query, not as an infallible filter. If a successful `business_type="article"` response has `data.count=0`, state that one extra paid fallback call will be made, repeat the same query/sort/time with `business_type="all"`, and filter `data.items` locally. Keep an item only when its `doc_url` host is exactly `mp.weixin.qq.com`; if `doc_url` is absent, accept it only when both `mpScene=7` and `src_type=49`. Exclude items carrying `exportId`. Never label generic web pages, news results, or Channels videos as Official Account articles.

Use relevance sorting unless the request is time-sensitive. For “最新/最近/刚发布”, prefer latest sorting plus the narrowest supported time filter. Do not compare engagement numbers across platforms as if they were equivalent.

## Normalize and return

Return a compact result list grouped by platform. Use these fields when available:

- `platform`
- `content_type`: `note`, `video`, or `official_account_article`
- `title`
- `summary`
- `author`
- `published_at`
- `url`
- `metrics`
- `platform_id`
- `query`
- `captured_at`

Deduplicate only within a platform, using a stable platform ID first and canonical URL second. Keep missing fields null or omit them; never invent values.

For an ordinary search response, show title, author, date, a short snippet, useful metrics, and a clickable source link. State which platforms failed or returned no results. Do not automatically produce a research report, evidence cards, sentiment labels, or a long methodology section.

## Expand selected results only

When the user asks for details or comments, expand only supplied links/IDs or results the user selected. Relevant capabilities include:

- Xiaohongshu note details and public note comments;
- Douyin video details and public video comments;
- WeChat Official Account article detail, stats, public comments/replies, related articles, account profile, and account article list.

Do not fetch comments for every search result by default. For comment collection, return the source item with its comments so context is not lost, and anonymize ordinary commenters in summaries unless identity is necessary.

## REST fallback

If MCP is unavailable, read [setup.md](references/setup.md) and use `scripts/tikhub_api.py`. Its default is a no-cost dry run. Confirm the current REST endpoint and schema in TikHub's official OpenAPI/docs before execution.

## Boundaries

- Use only public, permitted surfaces. Do not bypass privacy, deletion, authentication, or access controls.
- Never ask the user to paste an API key into chat or write it into the repository.
- Do not perform likes, follows, replies, posting, messaging, or other account actions.
- Treat search results as platform-ranked samples, not population statistics.
- When technical correctness matters, use social results as discovery leads and verify factual claims against primary sources if the user asks for conclusions.
