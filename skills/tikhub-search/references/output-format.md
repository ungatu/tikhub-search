# Unified search output

Use this schema for saved JSON or structured handoffs. Search responses do not need every field.

```json
{
  "query": "关键词",
  "platforms": ["xiaohongshu", "douyin", "wechat"],
  "captured_at": "2026-08-27T14:00:00+08:00",
  "results": [
    {
      "platform": "wechat",
      "content_type": "official_account_article",
      "platform_id": null,
      "title": "文章标题",
      "summary": "简短摘要",
      "author": "公众号名称",
      "published_at": null,
      "url": "https://mp.weixin.qq.com/s/...",
      "metrics": {},
      "query": "关键词",
      "captured_at": "2026-08-27T14:00:00+08:00"
    }
  ],
  "status": {
    "xiaohongshu": "ok",
    "douyin": "ok",
    "wechat": "ok"
  }
}
```

## Display rules

- Group by platform and preserve platform rank.
- Show at most the requested count; otherwise show the useful first-page results.
- Prefer canonical public URLs over temporary media URLs.
- Keep metrics as named values such as `likes`, `comments`, `collects`, `shares`, `views`, or `reads` only when present.
- Do not calculate one cross-platform popularity score.
- Mark unavailable dates or metrics as unknown rather than guessing.
- Include a short partial-failure note when any platform status is not `ok`.

For CSV, flatten known metric keys into columns and serialize uncommon metrics as JSON in `metrics_json`.
