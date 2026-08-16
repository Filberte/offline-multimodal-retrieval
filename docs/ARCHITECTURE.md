# Architecture

## System context

The application is an offline desktop-first local retrieval system. A Flutter UI manages Library, Search, and Settings workflows. A Python backend parses local files, builds text and image embeddings through locally configured model adapters, stores vectors in Chroma, computes BM25 keyword scores, and returns hybrid-ranked results.

External actors are limited to the end user, the local file system, user-supplied optional models, and the operating system. There is no production cloud service, analytics endpoint, credential store, or network API.

## Component view

- Week 2 ingestion: path validation and TXT/PDF/DOCX/JPG/PNG parsing.
- Week 3 embeddings: BERT TFLite text adapter (768 dimensions) and MobileCLIP visual adapter (512 dimensions), both locally configured.
- Week 4 retrieval: Chroma persistence, BM25, normalization, and hybrid score `0.7 × semantic + 0.3 × keyword`.
- Week 5 UI: independent desktop, tablet, and mobile compositions with keyboard and semantic accessibility.
- Week 6 integration: JSON-lines standard-input/output bridge, cache, health, performance, and security utilities.
- Week 7 release layer: preflight, documentation drift checks, direct-dependency SBOM, OSS policy, and go/no-go gates.

## Data flow

1. The user selects a local folder.
2. The UI sends `index_paths` for selected paths or `index_directory` for a directory through the existing local process bridge.
3. The backend resolves and validates paths, parses supported files, creates embeddings, and persists local index records.
4. A query travels through the same bridge to `search`.
5. The service calculates semantic and BM25 scores, applies filters, ranks results, and serializes only the result metadata required by the UI.
6. The UI displays result cards and local paths. No indexed content leaves the device through application code.

## Security boundary

The trust boundary encloses the Flutter process, Python child process, configured local index, and user-authorized source paths. JSON-lines messages are size/shape validated and no TCP/HTTP listener is bound. Paths are canonicalized before access. Credentials are neither required nor stored.

User-supplied documents, models, native dependencies, OS permissions, and backup systems remain untrusted inputs or external controls. Model files are excluded from the source distribution.

## Failure modes

The UI exposes backend ready/degraded state and actionable issues. Unsupported process platforms enter labelled demo mode instead of pretending to execute production retrieval. Index corruption is handled through backup/rebuild; model dimension changes require a separate compatible index.

## Scalability and performance

The architecture targets single-device personal collections, not multi-tenant enterprise search. Query and embedding caches are bounded LRU structures. Week 6 reference performance uses a deterministic hashing backend to measure application overhead; it must not be interpreted as BERT/MobileCLIP inference latency.
