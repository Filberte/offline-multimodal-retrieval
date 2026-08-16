# Contributing

Use Python 3.12+ and the repository-local Flutter toolchain. Keep the application offline-only, preserve keyboard and screen-reader semantics, and add a continuously numbered test for every behavior change.

1. Run `python run_tests.py` from the Week7_Deliverables directory.
2. Confirm 500/500 tests, Python core coverage at least 90%, and Flutter source coverage at least 80%.
3. Run `python run_release_readiness.py` and resolve every blocking gate.
4. Update architecture, API, user, accessibility, maintenance, and compliance documentation when behavior changes.
5. Do not commit model weights, validation datasets, secrets, caches, or compiled build output.

Contributions are submitted under the project Apache-2.0 license unless explicitly stated otherwise.
