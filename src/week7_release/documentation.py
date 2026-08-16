"""Documentation manifest, heading coverage, and local-link validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import DocumentationAudit, DocumentationEntry

_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def default_documentation_manifest() -> tuple[DocumentationEntry, ...]:
    """Return the release documentation contract shared by tests and packaging."""

    return (
        DocumentationEntry("docs/ARCHITECTURE.md", "Architecture", "Maintainers", ("System context", "Data flow", "Security boundary")),
        DocumentationEntry("docs/API_REFERENCE.md", "API reference", "Integrators", ("Transport", "Methods", "Errors")),
        DocumentationEntry("docs/INSTALLATION.md", "Installation", "End users", ("Requirements", "Install", "Verify", "Uninstall")),
        DocumentationEntry("docs/USER_GUIDE.md", "User guide", "End users", ("Index content", "Search", "Troubleshooting")),
        DocumentationEntry("docs/ACCESSIBILITY_GUIDE.md", "Accessibility", "End users", ("Keyboard", "Display", "Known limitations")),
        DocumentationEntry("docs/MAINTENANCE.md", "Maintenance", "Maintainers", ("Operations", "Backup", "Upgrade", "Rollback")),
        DocumentationEntry("docs/RELEASE_CHECKLIST.md", "Release checklist", "Release managers", ("Quality gates", "Compliance gates", "Sign-off")),
        DocumentationEntry("docs/TROUBLESHOOTING.md", "Troubleshooting", "Support", ("Startup", "Indexing", "Search", "Diagnostics")),
    )


def markdown_headings(text: str) -> tuple[str, ...]:
    """Extract ATX headings while ignoring fenced code blocks."""

    headings: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and re.match(r"^#{1,6}\s+", line):
            headings.append(re.sub(r"^#{1,6}\s+", "", line).strip().rstrip("#").strip())
    return tuple(headings)


def local_markdown_links(text: str) -> tuple[str, ...]:
    """Extract only relative local file links, excluding anchors and web URLs."""

    links = []
    for raw in _LINK.findall(text):
        target = raw.strip().split("#", 1)[0]
        if target and "://" not in target and not target.startswith(("#", "mailto:")):
            links.append(target.replace("%20", " "))
    return tuple(links)


def audit_documentation(root: Path, entries: Iterable[DocumentationEntry]) -> DocumentationAudit:
    """Validate every documented file, required heading, and relative link."""

    specs = tuple(entries)
    missing_files: list[str] = []
    missing_headings: list[str] = []
    broken_links: list[str] = []
    present = 0
    for entry in specs:
        path = root / entry.path
        if not path.is_file():
            missing_files.append(entry.path)
            continue
        present += 1
        text = path.read_text(encoding="utf-8")
        headings = {item.casefold() for item in markdown_headings(text)}
        for heading in entry.required_headings:
            if heading.casefold() not in headings:
                missing_headings.append(f"{entry.path}#{heading}")
        for link in local_markdown_links(text):
            if not (path.parent / link).resolve().exists():
                broken_links.append(f"{entry.path}->{link}")
    return DocumentationAudit(len(specs), present, tuple(missing_files), tuple(missing_headings), tuple(broken_links))
