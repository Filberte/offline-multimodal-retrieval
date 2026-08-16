# Offline Accessible Multimodal Local Retrieval — 1.0.0

Week 8 is the production hand-off of the eight-week internship project. The repository is self-contained for source imports and preserves the full contribution chain: Week 1 requirements/data/risk; Week 2 parsing; Week 3 offline embeddings; Week 4 Chroma and hybrid retrieval; Week 5 Flutter and accessibility; Week 6 integration/performance/security; Week 7 documentation/compliance/release gates; Week 8 executable delivery, cross-platform CI, demo, portfolio, and interview hand-off.

## Windows validation baseline

Windows is the real host build and demonstration target. The final demo uses exact files selected from the Week 1 local SQuAD, Wikipedia, COCO, and RVL-CDIP-related subsets. Run `scripts\01_prepare_week1_demo.ps1`, then `scripts\02_validate_week1_demo.ps1`, then `scripts\03_build_windows_release.ps1` from PowerShell.

## Evidence boundary

macOS and Linux source/configuration checks executed on Windows are simulations only. They are never presented as native builds, signatures, notarization, VoiceOver sessions, or real-machine launch evidence. The included GitHub Actions workflow is the authorized path to create native artifacts on `windows-latest`, `macos-latest`, and `ubuntu-latest` after the repository owner publishes the source.

## Demo video

The five-minute Windows demonstration follows the W8-DEMO-04 runbook (four fixed
queries over the Week 1 datasets, accessibility walkthrough, evidence summary).

- Video link: _pending — will be added here after the owner records it._

## Governance

- [Scope decisions and deviation record](docs/SCOPE_DECISIONS_AND_WAIVERS.md) —
  every approved deviation from the original specification (platform scope,
  usability-testing scope, dataset substitution, parsing/inference stack, coverage
  accounting), with rationale and sign-off status.
- [Manual accessibility test checklist](docs/ACCESSIBILITY_MANUAL_TEST_CHECKLIST.md) —
  NVDA screen-reader, keyboard-only, and display-adaptation test procedure that
  complements the automated WCAG 2.1 AA audit.

## Release gates

- 600 continuously numbered automated tests (`TC-001`–`TC-600`).
- Python core coverage at least 90%; Flutter source coverage at least 80%.
- Windows release executable, runtime assets, one-click launcher, and Week 1 dataset demo evidence.
- Full Week 1–8 lineage, OSS/data/model disclosure, portfolio manifest, and SHA-256 build manifest.
- Public GitHub publication and the five-minute video remain owner-controlled external actions.
