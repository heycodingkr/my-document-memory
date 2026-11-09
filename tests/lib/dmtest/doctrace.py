"""Spec to test traceability: every test ID that a spec cites must be defined in a docs/test document.

Doc-first rule (docs/test/README.md principle 1): IDs are agreed in the docs before code uses them. An ID is
defined by a table row (| MEM-01 |) or a heading (### FLOW-01) anywhere under docs/test. Citations may be
ranges (MEM-01~02, SEC-A01~A04) or lists (INST-43/44). Only prefixes that some test document defines are
checked, so spec-local requirement IDs (F-MEM-01) and external names are ignored.

    PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace docs/spec/memory.md docs/spec/recall.md
    PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# SEC-A01 style group letters (A-J) are part of the number token.
_NUM = r"[A-J]?\d{2,3}"
DEF_ROW = re.compile(r"^\|\s*([A-Z]{2,6}-" + _NUM + r")\s*\|", re.M)
DEF_HEAD = re.compile(r"^#{2,4}\s+([A-Z]{2,6}-" + _NUM + r")\b", re.M)
REF = re.compile(r"(?<![A-Za-z-])([A-Z]{2,6})-(" + _NUM + r")((?:[~/]" + _NUM + r")*)")
_TOKEN = re.compile(r"[~/]|[A-J]?\d+")


def _split(token):
    """'A01' -> ('A', 1, 2) ; '07' -> ('', 7, 2)"""
    letter = token[0] if token[0].isalpha() else ""
    digits = token[len(letter):]
    return letter, int(digits), len(digits)


def expand(prefix, first, tail):
    """Expand a citation into concrete IDs. Ranges (~) are inclusive; lists use /."""
    letter, number, width = _split(first)
    ids = [(letter, number, width)]
    previous, op = (letter, number, width), None
    for token in _TOKEN.findall(tail):
        if token in "~/":
            op = token
            continue
        t_letter, t_number, t_width = _split(token)
        t_letter = t_letter or previous[0]
        if op == "~":
            ids.extend((t_letter, n, t_width) for n in range(previous[1] + 1, t_number + 1))
        else:
            ids.append((t_letter, t_number, t_width))
        previous = (t_letter, t_number, t_width)
    return [f"{prefix}-{l}{n:0{w}d}" for l, n, w in ids]


def defined_ids(test_root=None):
    root = Path(test_root) if test_root else REPO / "docs" / "test"
    found = set()
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        found.update(DEF_ROW.findall(text))
        found.update(DEF_HEAD.findall(text))
    return found


def references(path):
    text = Path(path).read_text(encoding="utf-8")
    refs = []
    for match in REF.finditer(text):
        refs.extend(expand(match.group(1), match.group(2), match.group(3)))
    return refs


def undefined(paths, test_root=None):
    """(file, id) pairs cited by the given docs whose prefix is a defined test prefix but whose id is not defined."""
    defined = defined_ids(test_root)
    prefixes = {i.rsplit("-", 1)[0] for i in defined}
    problems = []
    for path in paths:
        for ref in sorted(set(references(path))):
            if ref.rsplit("-", 1)[0] in prefixes and ref not in defined:
                problems.append((str(path), ref))
    return problems


# Documents whose DOC-/SLIDE-/SHEET-nn numbers are seed-catalog item ids, not test ids (docs/spec/README.md).
NOT_TRACED = {"template-library.md"}


def all_docs():
    docs = REPO / "docs"
    return sorted(p for p in docs.rglob("*.md") if "demo" not in p.parts and p.name not in NOT_TRACED)


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    paths = all_docs() if args == ["--all"] else [Path(p) for p in args]
    problems = undefined(paths)
    for path, ref in problems:
        print(f"UNDEFINED {ref}  cited in {path}")
    print("OK: every cited test ID is defined" if not problems else f"{len(problems)} undefined citation(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
