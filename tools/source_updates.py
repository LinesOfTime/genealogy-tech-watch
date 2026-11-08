"""Validate source-backed editorial updates without mutating catalog scores."""
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

STATUSES = {"needs_recheck", "source_verified", "source_verified_with_gap"}
REQUIRED = ("project", "checked_at", "kind", "status", "summary", "verified",
            "limitations", "next_action", "sources")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_RE = re.compile(r"^/[^/]+/[^/]+/blob/([0-9a-f]{40})/.+$")


def validate_source_updates(root, catalog):
    """Return structured errors; missing/corrupt file blocks publication."""
    root = Path(root)
    issues = []
    def add(location, message):
        issues.append(dict(level="error", code="source_update", location=location, message=message))
    path = root / "docs/source-updates.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        add("docs/source-updates.json", str(exc))
        return issues
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("items"), list):
        add("docs/source-updates.json", "Expected schema version 1 and items array")
        return issues
    names = {str(x.get("name", "")).lower() for x in catalog if isinstance(x, dict)}
    seen = set()
    for i, row in enumerate(data["items"]):
        where = f"docs/source-updates.json:items[{i}]"
        if not isinstance(row, dict):
            add(where, "Expected object")
            continue
        for field in REQUIRED:
            value = row.get(field)
            if field == "sources":
                if not isinstance(value, list) or not value:
                    add(where + ".sources", "Require nonempty URLs")
            elif not isinstance(value, str) or not value.strip():
                add(where + "." + field, "Require nonempty text")
        name = str(row.get("project", "")).lower()
        if name not in names:
            add(where + ".project", "Project not present in root catalog")
        if name in seen:
            add(where + ".project", "Duplicate project update")
        seen.add(name)
        try:
            date.fromisoformat(row["checked_at"])
        except (ValueError, TypeError, KeyError):
            add(where + ".checked_at", "Invalid ISO date")
        if row.get("status") not in STATUSES:
            add(where + ".status", "Unknown status")
        commit = row.get("commit")
        if commit is not None and (not isinstance(commit, str) or not SHA_RE.fullmatch(commit)):
            add(where + ".commit", "Invalid commit SHA")
        for j, url in enumerate(row.get("sources", []) if isinstance(row.get("sources"), list) else []):
            loc = where + f".sources[{j}]"
            try:
                parts = urlsplit(url)
                valid = (parts.scheme == "https" and parts.hostname == "github.com"
                         and not parts.username and not parts.password and not parts.fragment)
            except (ValueError, TypeError, AttributeError):
                valid = False
            if not valid:
                add(loc, "Expected HTTPS github.com source")
                continue
            if row.get("status") != "needs_recheck":
                match = SOURCE_RE.fullmatch(parts.path)
                if not match or not commit or match.group(1) != commit:
                    add(loc, "Verified claim requires blob URL pinned to matching commit")
    return issues
