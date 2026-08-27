# Publishing checklist

## GitHub distribution

1. Create a public GitHub repository named `tikhub-search`.
2. Replace `YOUR_GITHUB_USERNAME` in `README.md` with the real account or organization.
3. After the repository exists, add its HTTPS `repository` and `homepage` URLs to `.codex-plugin/plugin.json`.
4. Review the publisher name and public support contact.
5. Run the tests, validators, and secret scan below.
6. Commit, push, and create a `v0.2.1` release.
7. In a fresh Codex task, install `skills/tikhub-search` from the public GitHub URL with `$skill-installer`.
8. Connect all three MCP servers and smoke-test one query on Xiaohongshu, Douyin, and WeChat Official Accounts.

Do not commit API keys, TikHub responses, personal account data, local absolute paths, or private research artifacts.

## OpenAI Plugins Directory

This repository is designed as a skills-only plugin. It does not own or proxy TikHub's hosted MCP domain, so do not submit TikHub's MCP server as if it were operated by this project.

1. Complete publisher identity verification and obtain the required Apps Management permission.
2. Prepare a production-ready logo and publish stable HTTPS pages for the repository, support, privacy policy, and terms.
3. Open <https://platform.openai.com/apps-manage> and create a skills-only plugin.
4. Upload the tested `skills/tikhub-search` bundle using the same file tree tested locally.
5. Use `submission/listing.md` and the five positive plus three negative cases from `submission/test-cases.md`, including result shapes and reproducible fixtures.
6. Choose only supported countries or regions, add release notes, complete policy attestations, and submit for review.
7. After approval, choose when to publish; review approval does not publish automatically.

Official process: <https://developers.openai.com/plugins/deploy/submission>

## Local validation

From this repository root:

```bash
python3 -m unittest discover -s tests -v

python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/tikhub-search

python3 /path/to/plugin-creator/scripts/validate_plugin.py .

rg -n -i 'bearer [a-z0-9._-]{12,}|api[_-]?key.{0,8}[=:].{0,4}[a-z0-9._-]{16,}' .
```

Review secret-scan matches manually. Environment-variable names and placeholder examples are expected; real credentials are not.

## Release maintenance

- Update the manifest version with semantic versioning.
- Recheck all three MCP tool schemas, WeChat `business_type` values, REST paths, pricing language, and publication rules.
- Re-run local installation and all test cases in a fresh task.
- Submit a new plugin version; published snapshots do not update automatically.
