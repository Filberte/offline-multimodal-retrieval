# Third-party notices

This file inventories direct runtime and development dependencies reviewed for the Week 7 release candidate. Transitive dependencies remain governed by their upstream licenses and are captured by the generated direct-component SBOM plus package lock files.

| Component | Reviewed version | License | Distribution action |
|---|---:|---|---|
| Python | 3.12 | PSF-2.0 | Runtime supplied by user |
| Chroma | 1.5.9 | Apache-2.0 | Dependency, preserve license/notice |
| NumPy | 2.4.4 | BSD-3-Clause | Dependency, preserve copyright/license |
| Pillow | 12.2.0 | MIT-CMU | Dependency, preserve copyright/license |
| pypdf | 6.14.2 | BSD-3-Clause | Dependency, preserve copyright/license |
| LiteRT | 2.1.5 | Apache-2.0 | Optional runtime, preserve license/notice |
| Transformers | 4.57.6 | Apache-2.0 | Optional model tooling |
| OpenCLIP | 3.3.0 | MIT | Optional model tooling |
| timm | 1.0.28 | Apache-2.0 | Optional model tooling; weights reviewed separately |
| PyTorch / torchvision | 2.10.0 / 0.25.0 | BSD-3-Clause | Optional conversion tooling |
| Flutter | 3.x | BSD-3-Clause | UI framework and toolchain |
| Offline Retrieval CJK (Noto Sans SC subset) | 2026-08 | SIL Open Font License 1.1 | Renamed static subset; Noto reserved name removed; OFL retained beside asset |

No third-party model weights, validation datasets, or original dataset samples are included in the Week 7 source archive. See [MODEL_AND_DATA_LICENSES.md](MODEL_AND_DATA_LICENSES.md) for the separate model/data decision record.

Before redistributing a compiled binary, regenerate the dependency inventory from the locked environment, retain each upstream license, and review transitive native assets. This file is an engineering compliance record, not legal advice.
