# Data quality summary

Data version: `a821cbd2717d338db09a87718909dccc1a4845a5e166fbdcff9418899b212fd9`.

Automated checks: 367; failures: 0.
Open gaps by priority: {'P0': 78, 'P1': 18}.
All gap statuses: {'archive_available_multipart': 1, 'open': 96, 'retired_scope_erratum': 1}.

## Deliberately retained limitations

- Unknown coordinates and fees remain missing; transformed coordinates are estimates, not surveyed gates.
- Three K7 route records remain archived and excluded; no unresolved candidate becomes an accepted entity.
- Historical G12 is retired after the teacher erratum; no two-community comparison is enforced.
- Housing CSV historical hash difference is explained by LF/CRLF bytes; originals were not rewritten.
- Source availability is separate from fact validity: reference-only and failed historical downloads remain visible.
- The original traffic script reproduces its four derived CSVs byte-for-byte in a disposable directory.
- Imported verified facts describe external declarations; review quarantine and original source availability.

## Review files

- `data/research_gaps.csv`: priority, entity, original evidence, needed information and task status.
- `data/import_quarantine.csv`: retained original incoming rows and rejection reasons.
- `quality_report.json`: every automated check and its result.
- `run_manifest.json`: pinned inputs, code/data version and generated artifact hashes.
