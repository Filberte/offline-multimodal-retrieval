# API reference

## Compatibility baseline

Week 7 preserves the Week 6 Flutter ↔ Python contract. Release-readiness, compliance, documentation, and preflight modules are additive internal Python APIs; they do not rename or replace the production bridge.

## Transport

The desktop client uses UTF-8 JSON Lines over the Python child process standard input and standard output. Each input line contains one request object and produces one response object. Diagnostics use standard error. The application does not open an HTTP service or network port.

Request envelope:

```json
{"request_id":"req-001","command":"health","data":{}}
```

Success envelope:

```json
{"ok":true,"request_id":"req-001","data":{"status":"ready"}}
```

Error envelope:

```json
{"ok":false,"request_id":"req-001","error":{"code":"invalid_request","message":"command is required"}}
```

## Methods

The Week 6 bridge calls these wire operations `command` values. The “Methods” heading is retained for the existing documentation contract; it does not rename the JSON field.

### `ping`

Data: `{}`. Returns `message` and `offline_only` for a lightweight bridge check.

### `health`

Data: `{}`. Returns `BackendHealth`: status, mode, offline-only flag, backend/vector-store identity, indexed count, uptime, cache statistics, runtime metrics, and issues.

### `library`

Data: `{}`. Returns `items`, a list of existing `RetrievalHit`-compatible library records.

### `search`

Data uses the existing `SearchQuery` JSON contract: `query`, `top_k`, `semantic_weight`, `keyword_weight`, `include_images`, and optional `modality`, `content_type`, `extension`, `document_id`, and `source_path` filters. Returns `SearchResponse`.

### `index_paths`

Data: required non-empty `paths` array and optional `continue_on_error`. Each path is canonicalized and checked by the local security policy. Returns `IndexingResult`.

### `index_directory`

Data: required `path`, optional `recursive` (default `true`), and optional `continue_on_error` (default `true`). Returns `IndexingResult`.

### `shutdown`

Data: `{}`. Returns an acknowledgement and requests graceful child-process termination.

## Data contracts

- `SearchResponse`: `query`, `hits`, `elapsed_ms`, `candidate_count`, `warnings`.
- `RetrievalHit`: `item_id`, `document_id`, `text`, `score`, `semantic_score`, `keyword_score`, `space`, `modality`, `source_path`, `file_name`, `content_type`, `chunk_index`, `metadata`.
- `IndexingResult`: `discovered_files`, `parsed_files`, `parse_failures`, `embedding_inputs`, `embedding_failures`, `persisted_vectors`, `success`.

## Errors

| Code | Condition | Caller action |
|---|---|---|
| `invalid_json` | Input is invalid JSON or is not an object | Correct serialization; do not retry unchanged |
| `invalid_request` | Required field, type, path policy, or command validation failed | Correct the request or select an allowed path |
| `backend_error` | Unexpected local backend failure | Record privacy-safe diagnostics and inspect health |
| `timeout` | Flutter client receives no response within 90 seconds | Cancel the pending call and show a timeout message |

## Naming and compatibility

Dart uses camelCase; JSON and Python use snake_case. `SearchQuery`, `SearchResponse`, `RetrievalHit`, `BackendHealth`, and `IndexingResult` remain compatible with Week 4–6. Additive fields must have defaults or remain optional. Callers ignore unknown additive fields. Breaking field or command changes require a coordinated protocol-version change.
