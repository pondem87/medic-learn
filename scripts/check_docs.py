"""Check repository-relative Markdown links (template placeholders are illustrative)."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
errors = []
paths = [
    *root.glob("*.md"),
    *root.glob("docs/**/*.md"),
    *root.glob("profiles/*.md"),
    *root.glob("docker/*.md"),
]
for path in paths:
    text = path.read_text()
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = link.split("#")[0]
        if not target or "://" in target or "<" in target or target.startswith("mailto:"):
            continue
        if not (path.parent / target).exists():
            errors.append(f"{path.relative_to(root)}: {link}")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Validated relative file links in {len(paths)} Markdown documents.")
