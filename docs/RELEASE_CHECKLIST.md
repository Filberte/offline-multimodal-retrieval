# Release checklist

## Quality gates

- [ ] Exactly 500 catalogued tests with continuous IDs `TC-001`–`TC-500`.
- [ ] Python core coverage is at least 90%.
- [ ] Flutter source coverage is at least 80%.
- [ ] Flutter analyze/build and Windows launch smoke test succeed.
- [ ] Desktop, tablet, and mobile critical flows have no overflow or broken interaction.
- [ ] Performance, memory, stress, security, and accessibility evidence is current.
- [ ] macOS compatibility simulation is labelled non-real-machine and any Xcode/signing/notarization/launch work remains explicitly pending.

## Compliance gates

- [ ] Apache-2.0 project license and NOTICE are present.
- [ ] Direct dependencies and versions match the generated inventory.
- [ ] Third-party license/notice obligations are retained.
- [ ] No pretrained weights or validation datasets are in the release archive.
- [ ] MobileCLIP model/data restrictions and timm weight caveat are recorded.
- [ ] The source archive contains no secrets, network listener, cache, or compiled output.

## Documentation gates

- [ ] Architecture, API, installation, user, accessibility, maintenance, release, and troubleshooting Markdown contracts pass.
- [ ] Manager technical suite, user manual, compliance report, demo script, test document, and API document are rendered and visually audited.
- [ ] Version, limitations, dates, metrics, and artifact names agree across all files.

## Sign-off

| Role | Decision | Evidence |
|---|---|---|
| AI Product Manager | Pending | Scope, limitations, user flow, demo readiness |
| Technical Manager | Pending | Architecture, tests, security, performance, maintainability |
| OSS/Release Reviewer | Pending | License inventory, exclusions, package audit |

Release only when `run_release_readiness.py` reports `GO` and the final seven-file directory passes its independent audit.
