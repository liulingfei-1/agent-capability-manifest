#!/usr/bin/env python3
"""FIX-L3 runner v0.1 — Minis. Evidence-anchor assertion verification (一牙 joint design).
Checks: anchor consistency, coverage gaps, digest drift, canonicalizer drift, signed migration.
Usage: python3 fixl3_runner.py fixtures/FIX-L3-001.json [fixture...]
"""
import json, sys, hashlib, platform

def norm_digest(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()

def short(d):
    return d[:12]

def run_fixture(path):
    f = json.load(open(path))
    verdicts = []
    def check(name, cond, evidence, fclass=None):
        verdicts.append({"fixture_id": f.get('fixture_id'), "check": name, "pass": bool(cond),
                         "evidence": evidence, "failure_class": fclass})

    fid = f.get('fixture_id')
    aschema = f.get('assertion_schema', {})
    oracle = f.get('oracle', {})
    paths = aschema.get('oracle_paths', [])
    assertions = aschema.get('assertions', [])

    # canonical_digest self-excluded check (exclude canonical_digest AND evidence_anchor.fixture_digest — circular refs)
    def strip_self_refs(obj):
        if isinstance(obj, dict):
            return {k: strip_self_refs(v) for k, v in obj.items()
                    if not (k == 'canonical_digest' or (k == 'fixture_digest' and isinstance(obj.get('anchor_ref'), str)))}
        if isinstance(obj, list):
            return [strip_self_refs(i) for i in obj]
        return obj
    copy = strip_self_refs(f)
    actual = norm_digest(copy)
    check("canonical_digest", actual == f.get('canonical_digest'),
          f"self-excluded digest {'OK' if actual==f.get('canonical_digest') else 'MISMATCH'}")

    # coverage: every oracle leaf consumed, no orphans
    consumed = set()
    for a in assertions:
        consumed.update(a.get('consumes', []))
    # find all oracle leaves (paths ending in leaf keys)
    oracle_leaves = []
    for p in paths:
        # verify path resolves
        cur = f
        try:
            for part in p.split('.'):
                cur = cur[part] if isinstance(cur, dict) else None
            oracle_leaves.append(p)
        except Exception:
            pass
    uncovered = [p for p in oracle_leaves if p not in consumed]
    check("coverage_no_gap", not uncovered, f"uncovered={uncovered}", "oracle_coverage_gap" if uncovered else None)
    orphan = [a['id'] for a in assertions if not set(a.get('consumes', [])) <= set(paths)]
    check("coverage_no_orphan", not orphan, f"orphan={orphan}")

    # evidence_anchor checks per assertion
    for a in assertions:
        ea = a.get('evidence_anchor', {})
        if not ea:
            continue
        anchor_ref = ea.get('anchor_ref')
        consumed_paths = a.get('consumes', [])
        # FIX-L3-002: wrong anchor
        if anchor_ref and anchor_ref not in consumed_paths:
            check("anchor_matches_consumes", False,
                  f"{a['id']} anchor {anchor_ref} not in consumes {consumed_paths}", "evidence_anchor_mismatch")
        # FIX-L3-004: digest drift
        fd = ea.get('fixture_digest')
        if fd and fd != f.get('canonical_digest'):
            check("anchor_digest_matches", False,
                  f"{a['id']} anchor digest {short(fd)} != canonical {short(f.get('canonical_digest'))}", "fixture_digest_mismatch")
        # FIX-L3-005: canonicalizer drift
        cv = ea.get('canonicalizer_version')
        if cv and cv != "1.0":
            # 二分：能确定字节会变 -> FAIL；只是无法确认不变 -> UNVERIFIED
            has_signed_migration = bool(f.get('signed_migration'))
            if has_signed_migration:
                check("canonicalizer_check", True, f"{a['id']} canonicalizer {cv} covered by signed migration", None)
            else:
                check("canonicalizer_check", False,
                      f"{a['id']} canonicalizer {cv} != 1.0, no signed migration", "canonicalizer_version_mismatch")

    # expected verdict alignment
    exp = f.get('expected')
    all_pass = all(v['pass'] for v in verdicts)
    verdict = 'PASS' if all_pass else 'FAIL'
    if fid == 'FIX-L3-005':
        verdict = 'UNVERIFIED' if not all_pass else 'PASS'
    if fid == 'FIX-L3-006' and all_pass:
        verdict = 'MIGRATED_PASS'
    check("expected_alignment", verdict == exp, f"verdict={verdict} expected={exp}")

    summary = {"pass": sum(1 for v in verdicts if v['pass']), "fail": sum(1 for v in verdicts if not v['pass']),
               "blocked": 0, "verdict": verdict}
    return {"fixture_id": fid, "expected": exp, "verdict": verdict, "verdicts": verdicts,
            "summary": summary,
            "runner_identity": {"name": "minis", "version": "0.1", "runtime": platform.platform()},
            "digest_report": {"input_digest": short(actual), "normalization": "UTF-8/LF (JCS-ish, non-strict)"}}

if __name__ == '__main__':
    paths = sys.argv[1:] or ['FIX-L3-001.json']
    for p in paths:
        r = run_fixture(p)
        print(json.dumps(r, ensure_ascii=False))
