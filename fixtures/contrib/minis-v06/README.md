# Minis v0.6 Third-Party Fixture Contribution

This directory is a portable contribution record for the 2026-08-17 CD-4c fixture exchange.
It contains no credentials, local paths, or executable fixture payloads beyond the already-public
canonical fixtures and runners in this repository.

## Pinned source

- Repository: https://github.com/liulingfei-1/agent-capability-manifest
- License: MIT
- Pinned commit: `f3eadfbfceb1eb681cea6052d7be17e27af1abe2`
- Canonicalization: strict JCS RFC 8785 profile, recursive NFC, UTF-8, compact JSON,
  lowercase SHA-256; fixture `canonical_digest` is self-excluded.

## Replay commands

```bash
python3 runners/fix005_runner.py fixtures/FIX-005_aging_and_digest.json
python3 runners/fix006_runner.py fixtures/FIX-006_promote_after_aging_boundary.json
```

The runner reads the fixture as data only. It does not execute fixture-provided code,
make network calls, read credentials, or modify the fixture.

## Acceptance boundary

- Compare raw fixture hash and canonical/input digest before comparing outputs.
- Preserve complete JSON reports and 64-character digests.
- Map `UNVERIFIED` to the receiving implementation's evidence-state equivalent (`INDET`),
  never directly to semantic `FAIL`.
- Public receipt field crosswalk: [`RECEIPT_SCHEMA_CROSSWALK_v0.1.md`](../../../docs/RECEIPT_SCHEMA_CROSSWALK_v0.1.md)
