# offline_retrieval_ui — Week 7 RC

Flutter client for the offline accessible multimodal local retrieval release candidate (`0.7.0+7`). It provides independent desktop, tablet, and mobile shells for Library, Search, and Settings/Support workflows.

## Product behavior

- Windows desktop uses a local standard-input/output JSON-lines bridge to the Python retrieval core.
- Unsupported process platforms show a clearly labelled read-only demonstration mode.
- Production UI icons are locally custom-painted vectors; no `Icons.*` or default `Icon()` calls are present.
- A renamed 198 KB OFL-1.1 CJK font subset prevents first-render Chinese fallback glyph flashes.
- Settings exposes backend/privacy state, accessibility controls, version, capability boundaries, license summary, and offline help paths.

## Run and validate

```powershell
flutter pub get
flutter analyze
flutter test --coverage --concurrency 1
flutter build windows --release
flutter build web --release
```

The parent `run_tests.py` is authoritative: 360 Python tests plus 140 Flutter tests, continuously numbered `TC-001`–`TC-500`.

## Accessibility

Keyboard shortcuts: `Ctrl+K` search; `Alt+1` Library; `Alt+2` Search; `Alt+3` Settings; standard Tab/Shift+Tab and Enter/Space activation. High contrast, reduced motion, semantics, visible focus, and 90%–200% text scaling are implemented. The release is WCAG 2.1 AA-aligned engineering work, not an independent certification.
