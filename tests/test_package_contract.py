#!/usr/bin/env python3

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "tikhub-search" / "SKILL.md"
SETUP = ROOT / "skills" / "tikhub-search" / "references" / "setup.md"
PLATFORMS = ROOT / "skills" / "tikhub-search" / "references" / "platforms.md"


class PackageContractTests(unittest.TestCase):
    def test_plugin_and_skill_identity_match(self):
        manifest = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        skill_text = SKILL.read_text(encoding="utf-8")
        self.assertEqual(manifest["name"], "tikhub-search")
        self.assertIn("\nname: tikhub-search\n", skill_text)

    def test_required_mcp_servers_are_documented(self):
        setup_text = SETUP.read_text(encoding="utf-8")
        for platform in ("xiaohongshu", "douyin", "wechat"):
            self.assertIn(f"https://mcp.tikhub.io/{platform}/mcp", setup_text)

    def test_wechat_defaults_to_official_account_articles(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        platform_text = PLATFORMS.read_text(encoding="utf-8")
        self.assertIn('business_type="article"', skill_text)
        self.assertIn('"business_type": "article"', platform_text)
        self.assertIn("Do not substitute WeChat Channels", skill_text)


if __name__ == "__main__":
    unittest.main()
