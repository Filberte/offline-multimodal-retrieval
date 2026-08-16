# Security policy

## Supported release

Week 7 release candidate `0.7.x` is the supported project line.

## Security boundary

The desktop UI communicates with the Python retrieval service through a local standard-input/standard-output JSON-lines bridge. The production path does not bind an HTTP listener, transmit indexed content, or require cloud credentials. Indexed content, vector data, and caches remain in a user-selected local directory.

## Reporting

Do not include private documents, credentials, model files, or personal data in a report. Record the affected version, reproduction steps, expected and observed behavior, and the smallest synthetic fixture that reproduces the issue. For this internship package, route the report through the assigned manager rather than a public issue.

## Out of scope

Security properties of user-supplied models, datasets, operating-system permissions, and third-party toolchains are outside the application trust boundary and must be evaluated separately.
