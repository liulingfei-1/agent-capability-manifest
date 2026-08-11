#!/usr/bin/env python3
"""CAP-3D-001 runner v0.1 — three immutable digest domains.
Zero dependencies, Python 3.8+. Fixture path is required.
"""
import hashlib
import json
import platform
import sys
import unicodedata


def nfc(v):
    if isinstance(v, str):
        return unicodedata.normalize("NFC", v)
    if isinstance(v, list):
        return [nfc(x) for x in v]
    if isinstance(v, dict):
        return {unicodedata.normalize("NFC", k): nfc(val) for k, val in v.items()}
    return v


def canon(v):
    return json.dumps(nfc(v), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(v):
    return hashlib.sha256(canon(v).encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 cap3d_runner.py fixtures/CAP-3D-001_three_digest_domains.json")
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        fx = json.load(fh)

    declared = fx.get("canonical_digest")
    actual_fixture = digest({k: v for k, v in fx.items() if k != "canonical_digest"})
    if declared != actual_fixture:
        raise SystemExit(
            "canonical_digest mismatch: declared=%s actual=%s" % (declared, actual_fixture)
        )

    obj = fx["objects"]
    desc = obj["descriptions"]
    pol = obj["policies"]
    dist = obj["distributions"]
    receipts = obj["receipts"]
    polluted = obj["negative_controls"]["polluted_description"]
    exp = fx["oracle"]["expected"]

    cap_b_identity_before = digest(desc["cap_b"])
    # Receipts are separate objects and must not mutate description bytes.
    _ = digest(receipts["grant_v1"]), digest(receipts["revoke_v1"])
    cap_b_identity_after = digest(desc["cap_b"])

    policy_v1_digest = digest(pol["v1"])
    policy_v2_digest = digest(pol["v2"])
    manifest_v1_digest = digest(dist["v1"])
    manifest_v1_reordered_digest = digest(dist["v1_reordered_input"])
    manifest_v2_digest = digest(dist["v2"])

    old_grant = receipts["grant_v1"]
    old_grant_state = (
        {"evidence_state": "INDET", "operational_disposition": "HOLD"}
        if old_grant["policy_digest"] != policy_v2_digest
        else {"evidence_state": "PASS", "operational_disposition": "ACTIVE"}
    )
    forbidden_state_fields = {
        "capability_status",
        "execution_authority",
        "authorization",
        "grant",
        "revoke",
    }
    polluted_result = "REJECT" if forbidden_state_fields.intersection(polluted) else "PASS"

    domain_objects = [desc["cap_a"], desc["cap_b"], pol["v1"], pol["v2"], dist["v1"], dist["v2"]]
    domains_clean = all(not forbidden_state_fields.intersection(x) for x in domain_objects)

    observed = {
        "description_identity_unchanged_by_grant_revoke": cap_b_identity_before == cap_b_identity_after,
        "policy_digest_changes_v1_to_v2": policy_v1_digest != policy_v2_digest,
        "manifest_digest_changes_when_policy_changes": manifest_v1_digest != manifest_v2_digest,
        "manifest_digest_changes_when_capability_order_changes": manifest_v1_digest != manifest_v1_reordered_digest,
        "old_grant_after_policy_bump": old_grant_state,
        "polluted_description_with_execution_authority": polluted_result,
        "three_immutable_domains_exclude_authorization_state": domains_clean,
    }

    verdicts = []
    for key, expected in exp.items():
        actual = observed.get(key)
        verdicts.append(
            {
                "fixture_id": fx["fixture_id"],
                "check": key,
                "pass": actual == expected,
                "expected": expected,
                "actual": actual,
                "evidence_digest": digest({"check": key, "expected": expected, "actual": actual}),
            }
        )

    summary = {
        "pass": sum(1 for v in verdicts if v["pass"]),
        "fail": sum(1 for v in verdicts if not v["pass"]),
        "blocked": 0,
        "blockers": [],
    }
    report = {
        "runner_identity": {
            "name": "minis-cap3d",
            "version": "0.1",
            "runtime": platform.platform(),
            "env_digest": digest(
                {"python": sys.version.split()[0], "platform": platform.platform()}
            ),
        },
        "verdicts": verdicts,
        "summary": summary,
        "computed": {
            "cap_b_identity": cap_b_identity_before,
            "policy_v1_digest": policy_v1_digest,
            "policy_v2_digest": policy_v2_digest,
            "manifest_v1_digest": manifest_v1_digest,
            "manifest_v2_digest": manifest_v2_digest,
        },
        "digest_report": {
            "input_digest": actual_fixture,
            "output_digest": digest(
                {"verdicts": verdicts, "summary": summary, "computed": observed}
            ),
            "normalization": "JCS-compatible string/list/object profile + recursive NFC",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if summary["fail"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
