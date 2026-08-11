#!/usr/bin/env python3
"""CI verification: run core regressions plus adversarial and three-digest fixtures.
Exit 0 = verified; exit 1 = any failure."""
import glob
import hashlib
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []


def norm_digest(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8").replace(b"\r\n", b"\n")).hexdigest()


def run_runner(name, runner, fixture, expected_prefix=None):
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, runner), os.path.join(BASE, fixture)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        report = json.loads(result.stdout)
    except Exception:
        failures.append(f"{name}: runner output not JSON: {result.stdout[:200]}")
        return
    if result.returncode or report.get("summary", {}).get("fail", 1) > 0:
        failures.append(f"{name}: FAIL verdicts {report.get('summary')}")
    else:
        print(f"{name}: PASS {report.get('summary')}")
    actual = report.get("digest_report", {}).get("input_digest", "")
    if expected_prefix and not actual.startswith(expected_prefix):
        failures.append(f"{name}: input_digest {actual[:16]} != expected {expected_prefix}")


run_runner("FIX-005", "runners/fix005_runner.py", "fixtures/FIX-005_aging_and_digest.json", "8cd161245579")
run_runner("FIX-006", "runners/fix006_runner.py", "fixtures/FIX-006_promote_after_aging_boundary.json", "40efe29f2235")

for index in range(1, 6):
    matches = glob.glob(os.path.join(BASE, f"fixtures/CL-ADV-00{index}_*.json"))
    if not matches:
        failures.append(f"CL-ADV-00{index}: fixture not found")
    else:
        run_runner(f"CL-ADV-00{index}", "runners/cl_adv_runner.py", os.path.relpath(matches[0], BASE))

run_runner(
    "CAP-3D-001",
    "runners/cap3d_runner.py",
    "fixtures/CAP-3D-001_three_digest_domains.json",
    "005abf8446d8",
)

f5 = json.load(open(os.path.join(BASE, "fixtures/FIX-005_aging_and_digest.json")))
if norm_digest({k: v for k, v in f5.items() if k != "canonical_digest"}) != f5.get("canonical_digest"):
    failures.append("FIX-005 canonical_digest mismatch")
else:
    print("FIX-005 canonical_digest OK:", f5["canonical_digest"][:16])

if failures:
    print("FAILURES:")
    for failure in failures:
        print(" -", failure)
    sys.exit(1)
print("ALL CHECKS PASSED")
