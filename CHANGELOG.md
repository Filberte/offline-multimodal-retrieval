# Changelog

## 0.7.0-rc1 — 2026-08-13

- Added release-readiness, preflight, documentation-drift, and OSS compliance gates.
- Added Apache-2.0 project license, notices, model/data boundary record, support and contribution guidance.
- Added end-user installation, operation, accessibility, troubleshooting, maintenance, architecture, API, and release-checklist documentation.
- Retained the Week 6 platform-facing application name `offline_retrieval_ui`; Week 7 changes are additive release-governance work.
- Kept Flutter's framework icon-font assets for built-in controls, while production icon calls continue to use the project's local custom vector glyphs (no `Icons.*` or default `Icon()` calls).
- Bundled a renamed 198 KB static subset of Noto Sans SC under OFL-1.1 to prevent CJK fallback glyph flashes without adding the 17.8 MB source font to the release.
- Added version/privacy/open-source/help content to the settings experience.
- Fixed one malformed Week 6 test comment without changing the tested behavior.
- Expanded the continuously numbered automated suite from 300 to 500 tests.
