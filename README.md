# TikHub Search

[中文](#中文) · [English](#english)

## 中文

TikHub Search 是一个给 Codex 使用的轻量 skill：通过 TikHub 搜索小红书、抖音和微信公众号，并把不同平台的结果整理成统一格式。

它只赋予搜索能力，不内置一套庞大的调研方法论。普通请求的流程是：理解关键词和平台 → 每个平台搜索首屏 → 返回标题、作者、时间、摘要、指标和原始链接。只有用户明确要求时，才继续翻页或展开选中内容的详情与公开评论。

### 必须支持的平台

- 小红书笔记
- 抖音视频/图文等综合内容
- 微信公众号文章

“公众号”默认调用微信文章搜索，不会混成视频号搜索。TikHub 的同一个 WeChat MCP 也提供视频号能力，但只有用户明确说“视频号”时才使用。

### 安装 skill

仓库发布到 GitHub 后，可以让 Codex 的 skill installer 安装：

```text
$skill-installer Install the tikhub-search skill from https://github.com/ungatu/tikhub-search/tree/main/skills/tikhub-search
```

也可以手动克隆并链接：

```bash
git clone https://github.com/ungatu/tikhub-search.git
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/tikhub-search/skills/tikhub-search" \
  "$HOME/.agents/skills/tikhub-search"
```

### 连接 TikHub

准备自己的 TikHub API key，并让 `TIKHUB_API_KEY` 对启动 Codex 的进程可见：

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

运行 `codex mcp list` 验证，然后重启 Codex 或新建任务。完整说明见 [setup.md](skills/tikhub-search/references/setup.md)。

### 使用示例

```text
$tikhub-search 搜索“AI 录音笔”的用户真实反馈，同时查小红书、抖音和微信公众号。
```

```text
$tikhub-search 找最近 7 天关于 React 20 的中文讨论，按最新排序；只返回链接和摘要。
```

```text
$tikhub-search 先搜“知识管理工具太复杂”，然后只展开最相关的 3 条内容和公开评论。
```

直接提出搜索请求时，默认执行每个平台首屏一次。继续翻页或批量抓详情/评论前，skill 会说明新增调用数量；如果用户已经给了页数或预算上限，则直接在范围内执行。

### REST 兜底

MCP 不可用时，内置客户端可预览或执行任意当前 TikHub REST 端点。默认是 dry run，不会发送请求：

```bash
python3 skills/tikhub-search/scripts/tikhub_api.py \
  GET /api/v1/tikhub/user/get_user_info
```

客户端只从环境变量读取密钥，输出会脱敏。使用前仍需核对 TikHub 当前端点、参数和价格。

### 发布

当前 `0.2.0` 是可在 GitHub 分发、可作为 skills-only plugin 验证的重构版本。GitHub 与 OpenAI Plugins Directory 的后续步骤见 [PUBLISHING.md](PUBLISHING.md)。商店文案和测试用例位于 [submission](submission/)。

本项目不提供 TikHub 账号或额度，也不隶属于 TikHub。用户需遵守 TikHub、目标平台和适用法律的要求。

## English

TikHub Search is a thin, read-only Codex skill for searching Xiaohongshu, Douyin, and WeChat Official Account articles through TikHub. It normalizes first-page results and expands selected public details or comments only on request.

Install the standalone skill from the GitHub path above, connect the three TikHub MCP servers with your own API key, then invoke `$tikhub-search` with a query. See the Chinese section for complete commands.

## License

[MIT](LICENSE)
