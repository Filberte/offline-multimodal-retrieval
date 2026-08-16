# Troubleshooting

## Startup

If the backend is degraded, confirm Python 3.12+, package installation, write access to the local data directory, and the configured backend path. Run `python run_release_readiness.py` and inspect the first failing check.

If the web/demo target is used, the process bridge may be unavailable by design. Use the validated Windows desktop target for production retrieval.

## Indexing

- “Path not allowed”: select an existing local folder and avoid device/system roots or unresolved links.
- Zero indexed files: confirm supported file types and read permission.
- Model error: verify the optional local model path and dimension; models are not bundled.
- Index mismatch: rebuild after an embedding model or dimension change.

## Search

- Empty results: confirm indexed count, remove restrictive filters, and try a shorter query.
- Slow first query: local model warm-up can dominate first-use latency; subsequent cached queries can be faster.
- Unexpected ranking: inspect semantic/keyword/combined scores and verify the documented hybrid weights.
- OCR expectation: image text extraction is not a completed feature; search uses available visual embeddings.

## Diagnostics

Record application version, platform, backend health payload, indexed count, selected model adapter, and a synthetic reproduction query. Do not share source documents, absolute private paths, index databases, model weights, or credentials.

For code-level diagnosis, run the 500-test suite and review `reports/core_test_run.txt`, `reports/flutter_test_run.txt`, `reports/combined_test_summary.json`, and the release-readiness JSON.
