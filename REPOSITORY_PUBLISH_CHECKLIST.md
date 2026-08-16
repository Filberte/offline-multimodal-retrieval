# Public repository publication checklist

This source tree is repository-ready but has not been published by the project owner.

## Required owner actions

1. Review the history and working tree for secrets, personal data, model weights, and restricted datasets.
2. Confirm that `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `MODEL_AND_DATA_LICENSES.md` match the material actually published.
3. Create the public repository under the intended account or organization.
4. Push the prepared source package and enable the cross-platform workflow in `.github/workflows/cross-platform-release.yml`.
5. Inspect Windows, macOS, and Linux workflow artifacts before making any native-platform release claim.
6. Add the final five-minute Windows demonstration video link to `README.md`.

## Evidence boundary

- Windows: locally built and executed on the project owner's Windows host.
- macOS/Linux: source/configuration contract simulation on Windows; native CI artifacts remain pending.
- Week 1 datasets and local model files are not redistributed through the public source package unless their licenses and sizes are reviewed separately.
