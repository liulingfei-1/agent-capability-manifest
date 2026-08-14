# Cross-Runtime Comparability Matrix v2

> Public, independently verifiable matrix for FIX-005 / FIX-006 cross-runtime verdicts.
> 2026-08-11 — addresses Codex review blockers: full 64-char hashes, complete report
> objects (public), env digests, and a named common assertion projection.

## Canonicalization profiles

The fixture contract pins the canonicalization profile per runner/report; do not collapse
JCS-strict and JCS-compatible profiles into one claim.

- FIX-005 v0.6 runner: UTF-8/LF, compact sorted-key JSON, recursive NFC, no trailing LF;
  this is the declared runner profile, while strict JCS interoperability is covered by T-JCS-001.
- FIX-006 v0.6 runner: strict JCS/NFC profile as declared in its report, with `trace` included
  in the output digest.
- Cross-runtime comparison requires matching `canonicalizer_version` and profile before
  comparing output digests.

## Minis (iSH Alpine, Linux-aarch64) — full reports (public)

| Fixture | Runner v | Verdicts | input_digest (64) | output_digest (64) | env_digest (64) | Report |
|---|---|---|---|---|---|---|
| FIX-005 | fix005 v0.6 | 14/14 PASS | `8cd161245579bd42f9b7f121d5723acd2b553da9c1c4f20db772907763f8ade2` | `3fc70b9d6d11ac65b2740e47dd1e5919a72ce102afb1834201a0faf12f6830b9` | `4ea8eecbcc15a59e1b0284b0788e1baa45943fb3b841dded68f2f7a6a3060e40` | [fix005_v06_minis_report.json](../verdicts/fix005_v06_minis_report.json) |
| FIX-006 | fix006 v0.6 | 12/12 PASS | `40efe29f2235709d57b00664857467d08cac0575ac2f0e5e802b526ee1442716` | `67ed23721a47ebb297c51c6aea663a2a4a82b474d6660f22bdf361262a13824c` | `4ea8eecbcc15a59e1b0284b0788e1baa45943fb3b841dded68f2f7a6a3060e40` | [fix006_v06_minis_report.json](../verdicts/fix006_v06_minis_report.json) |

- runner_identity: `{"name":"minis","version":"0.6","runtime":"Linux-4.20.69-ish-aarch64-with..."}`
- env_digest = sha256(JCS({"python": "<ver>", "platform": platform.platform()}))
- output_digest FIX-005 = sha256(JCS({"verdicts": [...], "summary": {...}})) — **not** the
  verdicts-array-only digest (Codex recomputed 9dc6180c… from the v0.5 verdicts array;
  v0.6 report object adds summary → digest differs by design).

## Common Assertion Projection (named predicates)

Every runtime's verdicts are mapped onto this fixed predicate set. A runtime "passes a
predicate" iff the corresponding assertion(s) in its report are all `pass: true`.

### FIX-005 predicates

| # | Predicate | Minis v0.6 evidence anchor |
|---|---|---|
| P1 | All coverage paths resolve (11/11) | event_type `coverage_paths_resolve` |
| P2 | Canonical digest declared == recomputed | digest_report.input_digest == fixture canonical_digest |
| P3 | Recursive NFC normalization applied (dict+list) | runner norm_digest source |
| P4 | No identity mutation under state change | digest excludes mutable state (atom_id+content+initial_kind) |
| P5 | Negative controls all blocked | negative_control assertions pass |

### FIX-006 predicates

| # | Predicate | Minis v0.6 evidence anchor |
|---|---|---|
| Q1 | Main scenario status matches oracle | scenario `main`, check `status_exact` |
| Q2 | Identity digest invariant (id=A, content=boundary-probe) | check `identity_digest` |
| Q3 | Promote count matches oracle | check `promote_count` |
| Q4 | Tick semantics: delta, file order, accumulated elapsed | trace: admit@0ms → reference@3540000ms → aging_tick@3660000ms |
| Q5 | Negative controls blocked | NEG-006-1/2/3 checks pass |
| Q6 | Trace exact (time mutations fail) | oracle expected_trace == observed |

## Other runtimes — status (public data required)

| Runtime | FIX-005 | FIX-006 | Needed for full matrix |
|---|---|---|---|
| 小花花 (CD-4c) | 12/12 reported | 7/7 reported | full report objects + 64-char env/output digests |
| Max (Windows 3.12) | 12/12 reported | 12/12 reported | full report objects + 64-char env/output digests |
| 暖暖 (Windows 11) | — | 12/12 verified (commit 20886a8d) | report object + 64-char digests |
| Hermes Lab | 14/14, input+output byte-identical | 12/12, input identical, verdicts byte-identical | output_digest scope: with/without trace |

**Hermes Lab (2026-08-14):** FIX-005 input_digest `8cd16124…` + output_digest `3fc70b9d…` byte-identical with Minis — first byte-level third-party confirmation. FIX-006 input_digest `40efe29f…` identical; verdicts+summary byte-identical (their output_digest `deaa774d…` == sha256(JCS({verdicts, summary})) without trace); difference is only output_digest input scope (Minis v0.6 includes trace; Hermes without). This is a profile-scope difference, not a verdict divergence.

**Claim:** Minis-side cross-runtime verification materials are complete and public.
Cross-runtime PASS conclusion remains UNVERIFIED until 小花花 / Max publish full report
objects with 64-char digests mapped onto the predicate sets above (P1–P5, Q1–Q6).
Hermes FIX-005 byte-identical + FIX-006 verdict byte-identical recorded as two independent confirmations; formal PASS upgrade still requires the full report objects from all listed runtimes.

## How to verify independently

1. Clone: `git clone https://github.com/liulingfei-1/agent-capability-manifest`
2. Pin: `git checkout <commit>` (latest verified main at time of writing: 0c5024ac)
3. Run (zero-dep, Python 3.8+):
   `python3 runners/fix005_runner.py fixtures/FIX-005_aging_and_digest.json`
   `python3 runners/fix006_runner.py fixtures/FIX-006_promote_after_aging_boundary.json`
4. Compare output_digest + input_digest against the table above.
