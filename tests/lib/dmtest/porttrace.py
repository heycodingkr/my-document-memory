"""HARN-17: check WAM source coverage and explicit document-port dispositions.

    PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream

This validates the inventory, not semantic equivalence or product functionality.
"""
import argparse
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[3]


def _relative(value):
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute() and ".." not in value.split("/"))


def _inside(root, relative):
    return _relative(relative) and (root / relative).resolve().is_relative_to(root.resolve())


def audit(manifest, destination, upstream=None, require_upstream=False):
    destination = Path(destination)
    report = {"errors": [], "sources": 0, "adapted": 0, "excluded": 0, "upstream_checked": False}
    errors = report["errors"]
    try:
        document = json.loads(Path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        errors.append("manifest_unreadable")
        return report
    if (not isinstance(document, dict) or type(document.get("schema_version")) is not int
            or document["schema_version"] != 1 or not isinstance(document.get("entries"), list)):
        errors.append("invalid_manifest")
        return report
    entries = document["entries"]
    if not entries:
        errors.append("empty_inventory")
    seen = set()
    for index, row in enumerate(entries):
        label = f"entry[{index}]"
        if not isinstance(row, dict):
            errors.append(f"invalid_row: {label}")
            continue
        source = row.get("source")
        if (not _relative(source) or not source.startswith(("docs/spec/", "docs/test/"))
                or not source.endswith(".md")):
            errors.append(f"invalid_source_path: {label}")
            continue
        if source in seen:
            errors.append(f"duplicate_source: {source}")
        seen.add(source)
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errors.append(f"missing_reason: {source}")
        disposition, targets = row.get("disposition"), row.get("targets")
        if disposition not in ("adapt", "exclude"):
            errors.append(f"invalid_disposition: {source}")
            continue
        report["adapted" if disposition == "adapt" else "excluded"] += 1
        if (not isinstance(targets, list) or (disposition == "adapt" and not targets)
                or (disposition == "exclude" and targets)):
            errors.append(f"invalid_targets: {source}")
            continue
        for target in targets:
            if not _inside(destination, target):
                errors.append(f"invalid_target_path: {source}")
            elif not (destination / target).is_file():
                errors.append(f"missing_target: {source} -> {target}")
    report["sources"] = len(seen)
    upstream = Path(upstream) if upstream is not None else None
    if upstream is None or not upstream.is_dir():
        if require_upstream:
            errors.append("upstream_unavailable")
        return report
    report["upstream_checked"] = True
    actual = {str(path.relative_to(upstream)) for section in ("spec", "test")
              for path in (upstream / "docs" / section).rglob("*.md") if path.is_file()}
    if not actual:
        errors.append("empty_upstream")
    for source in sorted(actual - seen):
        errors.append(f"unmapped_source: {source}")
    for source in sorted(seen - actual):
        errors.append(f"missing_source: {source}")
    for source in sorted(actual & seen):
        if not _inside(upstream, source):
            errors.append(f"invalid_source_path: {source}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=REPO / "contracts/wam-port.v1.json")
    parser.add_argument("--destination", type=Path, default=REPO)
    parser.add_argument("--upstream", type=Path, default=REPO.parent / "web-agentic-memory")
    parser.add_argument("--require-upstream", action="store_true")
    args = parser.parse_args(argv)
    report = audit(args.manifest, args.destination, args.upstream, args.require_upstream)
    for error in report["errors"]:
        print(f"ERROR {error}")
    print(f"{'FAIL' if report['errors'] else 'OK'}: {report['sources']} sources, "
          f"{report['adapted']} adapted, {report['excluded']} excluded; "
          f"upstream comparison {'checked' if report['upstream_checked'] else 'SKIP (unavailable)'}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
