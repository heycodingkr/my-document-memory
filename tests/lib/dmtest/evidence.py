"""Evidence of a run: target/e2e-logs/<suite>/<run-id>/ with meta.json, cases.jsonl, trace.jsonl, sinks/, summary.md.

Case rows never contain sentinel values or raw target output (only ids, verdicts and short reasons).
"""
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class RunDir:
    def __init__(self, suite, run_id=None, base=None):
        self.suite = suite
        self.run_id = run_id or time.strftime("%Y%m%d-%H%M%S") + f"-{os.getpid() % 10000:04d}"
        self.path = Path(base or ROOT / "target" / "e2e-logs") / suite / self.run_id
        (self.path / "sinks").mkdir(parents=True, exist_ok=True)
        self.rows = []

    def write_meta(self, meta):
        (self.path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def case(self, case_id, verdict, **fields):
        row = {"id": case_id, "verdict": verdict, **fields}
        self.rows.append(row)
        with open(self.path / "cases.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def trace(self, event, **fields):
        with open(self.path / "trace.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"t": round(time.time(), 3), "event": event, **fields}, ensure_ascii=False) + "\n")

    def sink(self, name, data):
        target = self.path / "sinks" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else str(data).encode("utf-8"))
        return target

    def write_summary(self, title="Run"):
        counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
        for r in self.rows:
            counts[r["verdict"].split("(")[0]] = counts.get(r["verdict"].split("(")[0], 0) + 1
        lines = [f"# {title}", "", f"run: `{self.run_id}`  pass: {counts['PASS']}  fail: {counts['FAIL']}  skip: {counts['SKIP']}", ""]
        for r in self.rows:
            detail = r.get("reason") or r.get("detail") or ""
            lines.append(f"- {r['verdict']} `{r['id']}`" + (f" — {detail}" if detail else ""))
        (self.path / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return counts
