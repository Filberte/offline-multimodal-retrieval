# Maintenance

## Operations

Monitor backend health, indexed-record count, cache statistics, average search latency, search failures, and local disk growth. The application has no cloud telemetry; operators must collect diagnostics locally and remove private content before sharing.

## Backup

Close the backend before copying the Chroma/index directory. Back up configuration and index data separately from source documents. Verify the backup can be restored to a temporary user directory before relying on it.

## Upgrade

1. Review [CHANGELOG.md](../CHANGELOG.md) and dependency/model license changes.
2. Regenerate the direct dependency inventory and run all 500 tests.
3. Back up the index and configuration.
4. Install beside the current version and run preflight.
5. Rebuild the index if the persistence schema, embedding dimension, or selected model changed.
6. Run a fixed query set and compare latency and result relevance.

## Rollback

Stop the new backend, restore the previous executable/source version, and point it only to an index created with the compatible schema/model. If compatibility is uncertain, restore the matching index backup or rebuild from original documents. Never downgrade in place over the only copy of an index.

## Dependency maintenance

Pin reviewed versions, inspect upstream security advisories, rerun license policy checks, and review transitive native dependencies before release. Model weights and validation datasets remain outside the source distribution.

## Incident response

Disconnect the affected device from shared storage if unauthorized content access is suspected, preserve privacy-safe logs, record the exact version and local configuration, rotate any unrelated exposed credentials, and notify the manager through the private reporting route in [SECURITY.md](../SECURITY.md).
