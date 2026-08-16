# Accessibility guide

## Keyboard

- `Ctrl+K`: focus search.
- `Alt+1`, `Alt+2`, `Alt+3`: Library, Search, Settings.
- `Tab` / `Shift+Tab`: move through focusable controls.
- `Enter` / `Space`: activate the focused control.
- `Escape`: dismiss a supported modal or transient panel.

Focus order follows the visible task flow. Custom-painted icons are decorative unless a semantic label is explicitly supplied; interactive controls expose text labels or tooltips.

## Display

High-contrast mode uses a dark surface, light text, and visible focus indicators. Text scaling supports 90%–200%, with mobile, tablet, and desktop layouts reflowing independently. Reduced-motion mode disables non-essential movement.

## Screen readers

Status changes use live-region semantics where appropriate. Result controls, search fields, filters, settings, and backend health actions have programmatic labels. The UI is engineered toward WCAG 2.1 AA-aligned behavior, but it is not represented as independently certified.

## Known limitations

- No formal usability study with disabled participants has been completed.
- NVDA, VoiceOver, Android Accessibility Scanner, WAVE, and platform high-contrast automation are not all available in the offline test environment.
- OCR and audio transcription are not complete production features.
- Very long paths or unbroken strings can still require horizontal review in platform dialogs outside Flutter control.

Report an accessibility issue with the platform, text scale, contrast setting, keyboard sequence, expected result, observed result, and a privacy-safe screenshot.
