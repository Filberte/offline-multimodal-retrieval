# User guide

## First launch

Open the app and review Settings → System and local privacy status. Desktop builds start the local Python bridge; unsupported process platforms can show a clearly labelled read-only demonstration mode and must not be presented as a production backend.

## Index content

1. Open Library and choose Add folder.
2. Select a local folder containing supported TXT, PDF, DOCX, JPG, or PNG files.
3. Confirm the visible path and start indexing.
4. Wait for the indexed count to update. Existing source files are read but not modified.

OCR for text embedded in images is not a completed production capability. Image retrieval uses the configured visual embedding path when available.

## Search

Open Search or press `Ctrl+K`. Enter a short natural-language query, choose filters when needed, and submit. Results combine semantic-vector and BM25 keyword signals using the configured hybrid weighting. Open a result only after confirming the displayed local path.

The system retrieves local content; it is not a generative assistant, RAG service, or autonomous agent. It does not create answers from the indexed corpus.

## Accessibility

Open Settings to enable high contrast, reduce animation, or adjust text scale from 90% to 200%. Keyboard navigation and semantic labels are supported. See [ACCESSIBILITY_GUIDE.md](ACCESSIBILITY_GUIDE.md).

## Privacy

The production desktop path uses local standard input/output and does not expose an application network port. Content and indexes stay on the device. Users remain responsible for operating-system permissions, encrypted storage, backup policy, and any locally supplied model.

## Troubleshooting

If the backend shows degraded status, refresh health, confirm Python and local paths, and review the error message. For indexing or search failures, follow [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and preserve only synthetic diagnostics when escalating.
