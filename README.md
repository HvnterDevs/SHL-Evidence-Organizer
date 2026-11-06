# Shadow Hunter Labs Evidence Organizer

A small, local-first starter tool for organizing evidence during an **authorized** penetration test or security assessment. It stores files on your machine and maintains a simple JSONL index. It does not scan, exploit, or connect to targets.

> Early scaffold: review the code and adapt it to your engagement procedures before using it with real client material.

## Features in this starter

- Create an engagement workspace with `evidence/` and a JSONL manifest.
- Add a local file with a finding ID, description, and optional note.
- List recorded evidence.
- Export a portable ZIP bundle containing the evidence and manifest.
- No cloud service, telemetry, or external dependencies at runtime.

## Quick start

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
shel-evidence init .\engagement-alpha --name "Engagement Alpha"
shel-evidence add .\engagement-alpha --finding F-001 --file .\screenshots\access-control.png --description "Access control evidence" --note "User A could view User B's record."
shel-evidence list .\engagement-alpha
shel-evidence export .\engagement-alpha --output .\engagement-alpha-evidence.zip
```

On macOS/Linux, activate with `source .venv/bin/activate` and run the same `shel-evidence` commands.

## Workspace layout

```text
engagement-alpha/
├── manifest.jsonl
└── evidence/
    └── <evidence-id>_<original-filename>
```

Each manifest row records an evidence ID, UTC timestamp, finding ID, original filename, stored filename, SHA-256 digest, description, and note. Keep client workspaces outside this source repository and do not commit real engagement data.

## Handling sensitive data

Evidence may contain credentials, tokens, personal information, or confidential client details. Use only with written authorization and within the agreed scope. Store workspaces in an approved encrypted location, restrict access, redact before sharing, and follow the client's retention and deletion requirements. The starter copies evidence as-is; it does not detect or redact secrets. Treat exported ZIP files as sensitive.

## Roadmap ideas

- Preview and redact common secrets in text evidence before export.
- Add screenshot annotation and evidence captions.
- Generate a client-friendly HTML index.
- Add import/export schema versioning and configurable retention helpers.

## Development

The implementation uses only the Python standard library. Run locally with `python -m shel_evidence.cli --help` after installing the package in editable mode.

## License

MIT. See [LICENSE](LICENSE).
