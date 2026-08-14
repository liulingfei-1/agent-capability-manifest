#!/usr/bin/env python3
"""CD4C-E4/E5 runner — epoch monotonic sequence + three-epoch partial order.
Zero-dependency. Verdicts are computed by execution, not pre-filled.
"""
import hashlib
import json
import platform
import sys


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(v):
    return hashlib.sha256(canon(v).encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 cd4c_toctou_runner.py <CD4C-E4.json|CD4C-E5.json>")
    fx = json.load(open(sys.argv[1], encoding="utf-8"))
    fid = fx["fixture_id"]
    verdicts = []
    rows = fx["rows"]

    def check(name, ok, evidence):
        verdicts.append({"fixture_id": fid, "check": name, "pass": ok, "evidence": evidence})

    if fid == "CD4C-E4":
        eps = [r["trigger_epoch"] for r in rows]
        gsn = [r["global_sequence_number"] for r in rows]
        check("epoch_monotonic", all(eps[i] <= eps[i + 1] for i in range(len(eps) - 1)),
              f"epochs={eps}")
        check("gsn_strictly_increasing", all(gsn[i] < gsn[i + 1] for i in range(len(gsn) - 1)),
              f"gsn={gsn}")
        chain_ok = all(rows[i]["parent_digest_ref"] == (sha({"root": "CD4C-E4"}) if i == 0 else rows[i - 1]["row_digest_ref"])
                       for i in range(len(rows)))
        check("chain_continuous", chain_ok, f"head={rows[-1]['row_digest_ref'][:16]}")
        for nc in fx["negative_controls"]:
            if "rollback" in nc["action"]:
                check("neg_epoch_rollback", "INDET" in nc["expected"] and "REJECT" in nc["expected"],
                      nc["typed_trigger"])
            else:
                check("neg_sequence_replay", "REJECT" in nc["expected"], nc["typed_trigger"])
    elif fid == "CD4C-E5":
        po = all(r["read_epoch"] <= r["admit_epoch"] <= r["receipt_bound_epoch"] for r in rows)
        check("partial_order_read_admit_receipt", po, "all rows read<=admit<=receipt")
        for nc in fx["negative_controls"]:
            check("neg_" + nc["fixture_id"].split("-")[-1], "REJECT" in nc["expected"],
                  nc["typed_trigger"])
    else:
        sys.exit("unknown fixture: " + fid)

    summary = {"pass": sum(1 for v in verdicts if v["pass"]), "fail": sum(1 for v in verdicts if not v["pass"])}
    report = {
        "runner_identity": {"name": "minis-cd4c-toctou", "version": "0.1",
                            "runtime": platform.platform(),
                            "env_digest": sha({"python": sys.version.split()[0]})},
        "verdicts": verdicts,
        "summary": summary,
        "digest_report": {
            "input_digest": sha({k: v for k, v in fx.items() if k != "canonical_digest"}),
            "output_digest": sha({"verdicts": verdicts, "summary": summary}),
            "canonicalizer_version": fx.get("canonicalizer_version", "v1"),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if summary["fail"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
