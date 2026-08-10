#!/usr/bin/env python3
"""CI verification: run FIX-005/006 runners, check verdicts all-pass and canonical digests.
Exit 0 = verified; exit 1 = any failure."""
import json, hashlib, subprocess, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []

def norm_digest(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canon.encode('utf-8').replace(b'\r\n', b'\n')).hexdigest()

def run_runner(name, runner, fixture, expect_input_prefix):
    r = subprocess.run([sys.executable, os.path.join(BASE, runner), os.path.join(BASE, fixture)],
                       capture_output=True, text=True, timeout=120)
    try:
        d = json.loads(r.stdout)
    except Exception:
        failures.append(f"{name}: runner output not JSON: {r.stdout[:200]}")
        return
    if d.get('summary', {}).get('fail', 1) > 0:
        failures.append(f"{name}: FAIL verdicts {d.get('summary')}")
    else:
        print(f"{name}: PASS {d.get('summary')}")
    inp = d.get('digest_report', {}).get('input_digest', '')
    if not inp.startswith(expect_input_prefix):
        failures.append(f"{name}: input_digest {inp} != expected prefix {expect_input_prefix}")

# FIX-005 v0.4
run_runner("FIX-005", "runners/fix005_runner.py", "fixtures/FIX-005_aging_and_digest.json", "8cd161245579")

# FIX-006 v0.2-locked
run_runner("FIX-006", "runners/fix006_runner.py", "fixtures/FIX-006_promote_after_aging_boundary.json", "b4c0243aeb01")

# canonical digest self-exclusion check
f5 = json.load(open(os.path.join(BASE, 'fixtures/FIX-005_aging_and_digest.json')))
d5 = {k: v for k, v in f5.items() if k != 'canonical_digest'}
if norm_digest(d5) != f5.get('canonical_digest'):
    failures.append("FIX-005 canonical_digest mismatch")
else:
    print("FIX-005 canonical_digest OK:", f5['canonical_digest'][:16])

if failures:
    print("FAILURES:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
