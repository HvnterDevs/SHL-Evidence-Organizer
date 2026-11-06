from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def workspace(path: Path) -> tuple[Path, Path]:
    root = path.expanduser().resolve()
    evidence = root / "evidence"
    manifest = root / "manifest.jsonl"
    if not evidence.is_dir() or not manifest.is_file():
        raise ValueError(f"Not an evidence workspace: {root} (run 'init' first)")
    return root, manifest


def cmd_init(args: argparse.Namespace) -> int:
    root = args.workspace.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(exist_ok=True)
    manifest = root / "manifest.jsonl"
    if manifest.exists() and manifest.stat().st_size:
        raise ValueError(f"Workspace already initialized: {root}")
    manifest.touch(exist_ok=True)
    metadata = {"workspace_name": args.name, "created_at_utc": now_utc(), "format_version": 1}
    (root / "workspace.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized {root}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    root, manifest = workspace(args.workspace)
    source = args.file.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("Evidence input must be a file")
    evidence_id = uuid.uuid4().hex[:12]
    stored_name = f"{evidence_id}_{source.name}"
    destination = root / "evidence" / stored_name
    shutil.copy2(source, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    record = {
        "evidence_id": evidence_id,
        "captured_at_utc": now_utc(),
        "finding_id": args.finding,
        "original_filename": source.name,
        "stored_filename": stored_name,
        "sha256": digest,
        "description": args.description,
        "note": args.note or "",
    }
    with manifest.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Added {evidence_id} ({digest})")
    return 0


def read_records(manifest: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid manifest JSON on line {line_number}: {exc}") from exc
    return records


def cmd_list(args: argparse.Namespace) -> int:
    _, manifest = workspace(args.workspace)
    records = read_records(manifest)
    if not records:
        print("No evidence recorded yet.")
    for item in records:
        print(f"{item['evidence_id']} | {item['finding_id']} | {item['original_filename']} | {item['captured_at_utc']}")
        print(f"  {item['description']}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    root, _ = workspace(args.workspace)
    output = args.output.expanduser().resolve()
    if output == root or root in output.parents:
        raise ValueError("Export ZIP must be outside the engagement workspace")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root.parent))
    print(f"Exported bundle to {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shel-evidence", description="Organize evidence locally for authorized assessments")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create an engagement workspace")
    init.add_argument("workspace", type=Path)
    init.add_argument("--name", required=True, help="engagement label; avoid unnecessary client identifiers")
    init.set_defaults(func=cmd_init)
    add = sub.add_parser("add", help="copy a file into the workspace and index it")
    add.add_argument("workspace", type=Path)
    add.add_argument("--finding", required=True, help="finding reference, such as F-001")
    add.add_argument("--file", required=True, type=Path)
    add.add_argument("--description", required=True)
    add.add_argument("--note", default="")
    add.set_defaults(func=cmd_add)
    listing = sub.add_parser("list", help="list indexed evidence")
    listing.add_argument("workspace", type=Path)
    listing.set_defaults(func=cmd_list)
    export = sub.add_parser("export", help="create a ZIP evidence bundle")
    export.add_argument("workspace", type=Path)
    export.add_argument("--output", required=True, type=Path)
    export.set_defaults(func=cmd_export)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.func(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
