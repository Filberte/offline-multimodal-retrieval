# Installation

## Requirements

- Windows 10/11 x64 is the primary validated desktop environment.
- The macOS target has passed only Windows-hosted static/configuration simulation; it is not a validated production target until Xcode build, signing, notarization, Gatekeeper, VoiceOver, Intel/Apple Silicon, and real-machine launch checks are completed.
- Python 3.12 or later for the local retrieval service.
- Flutter is needed only for development or rebuilding the desktop UI.
- At least 4 GB free disk space when optional local models are installed separately.
- No internet connection is required after dependencies and optional user-supplied models are installed.

## Install

1. Extract the Week 7 source archive to a user-writable local folder.
2. Create a Python virtual environment and install the declared dependencies from `pyproject.toml`.
3. Keep optional model weights outside the extracted source directory. Configure their local paths according to your approved model terms.
4. From `app/offline_retrieval_ui`, restore Flutter packages using the repository-local cache, then build or run the Windows target.
5. Do not run the application with administrator privileges unless the selected content directory specifically requires them.

Developer commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
python run_release_readiness.py
python run_tests.py
python scripts/run_macos_compatibility_simulation.py
```

The final command is optional and non-blocking for the Windows release. A 15/15 result confirms source/configuration contracts only; it must not be reported as a real macOS test pass.

## Verify

Run the release-readiness command. A valid package reports no missing source or notice files, no network-listener patterns, and no bundled model weights. In the UI, Settings → System and local privacy status should show local mode and no network endpoint.

## Uninstall

Close the UI and local backend. Remove the extracted application directory, then separately remove the user-selected Chroma/index directory if the local index is no longer needed. Original source documents are never deleted by the application.

## Upgrade

Back up the local index directory, extract the new version beside the old version, run preflight, then rebuild the index when the schema/version note requires it. See [MAINTENANCE.md](MAINTENANCE.md) for rollback.
