#!/usr/bin/env python3
"""CD4C-E4/E5 runner — spec-aligned 6-field row format.
Checks: envelope digest, row chain (parent_ascii || JCS), monotonicity/partial order,
negative controls declared FAIL. Zero-dependency.
"""
import hashlib
import json
import platform
import sys
import unicodedata
from decimal import Decimal

IJSON_INT_LIMIT = 2**53 - 1


def _jcs_number(n):
    if isinstance(n, bool):
        return "true" if n else "false"
    if isinstance(n, int):
        if abs(n) > IJSON_INT_LIMIT:
            raise ValueError("I-JSON range")
        return str(n)
    if isinstance(n, float):
        if n != n or n in (float("inf"), float("-inf")):
            raise ValueError("non-finite")
        if n == 0:
            return "0"
        s = format(Decimal(repr(n)), "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s if s != "-0" else "0"
    raise TypeError(type(n))


def _jcs_string(s):
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif o < 0x20:
            out.append(f"\\u{o:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _nfc(v):
    if isinstance(v, str):
        n = unicodedata.normalize("NFC", v)
        if n != v:
            raise ValueError("non-NFC")
        return v
    if isinstance(v, list):
        return [_nfc(x) for x in v]
    if isinstance(v, dict):
        return {_nfc(k): _nfc(val) for k, val in v.items()}
    return v


def jcs(value):
    value = _nfc(value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, Decimal)):
        return _jcs_number(value)
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, list):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-le"))
        return "{" + ",".join(jcs(k) + ":" + jcs(v) for k, v in items) + "}"
    raise TypeError(type(value))


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 cd4c_toctou_runner.py <CD4C-E4.json|CD4C-E5.json>")
    fx = json.load(open(sys.argv[1], encoding="utf-8"))
    fid = fx["envelope"]["payload"]["fixture_id"]
    verdicts = []
    rows = fx["rows"]

    def check(name, ok, evidence):
        verdicts.append({"fixture_id": fid, "check": name, "pass": ok, "evidence": evidence})

    # envelope digest
    md = fx["envelope"]["manifest_digest"]
    computed = sha256_hex(jcs(fx["envelope"]["payload"]).encode("utf-8"))
    check("envelope_manifest_digest", md == computed, f"{md[:16]} vs {computed[:16]}")

    # chain: row_digest = SHA256(parent_ascii || JCS(row minus row_digest_ref))
    parent = fx["envelope"]["header_digest"]
    chain_ok = True
    for row in rows:
        core = {k: v for k, v in row.items() if k != "row_digest_ref"}
        expected = sha256_hex(parent.encode("ascii") + jcs(core).encode("utf-8"))
        if row["row_digest_ref"] != expected or row["parent_digest_ref"] != parent:
            chain_ok = False
        parent = expected
    check("row_chain", chain_ok, f"head={rows[-1]['row_digest_ref'][:16]}")
    check("terminal_verdict_valid",
          all(r["terminal_verdict"] in {"PASS", "INDET", "FAIL", "UNKNOWN", "UNCLASSIFIED"} for r in rows),
          "5-value set")

    if fid == "CD4C-E4":
        eps = [r["trigger_epoch"] for r in rows]
        gsn = [r["global_sequence_number"] for r in rows]
        check("epoch_monotonic", all(eps[i] <= eps[i + 1] for i in range(len(eps) - 1)), f"epochs={eps}")
        check("gsn_strictly_increasing", all(gsn[i] < gsn[i + 1] for i in range(len(gsn) - 1)), f"gsn={gsn}")
    elif fid == "CD4C-E5":
        po = all(r["read_epoch"] <= r["admit_epoch"] <= r["receipt_bound_epoch"] for r in rows)
        check("partial_order", po, "read<=admit<=receipt")
    else:
        sys.exit("unknown fixture " + fid)

    for nc in fx.get("negative_controls", []):
        check("neg_" + nc["replay_seed"].split(":")[2], nc["terminal_verdict"] == "FAIL",
              nc.get("typed_trigger", ""))

    summary = {"pass": sum(1 for v in verdicts if v["pass"]), "fail": sum(1 for v in verdicts if not v["pass"])}
    report = {
        "runner_identity": {"name": "minis-cd4c-toctou", "version": "0.2",
                            "runtime": platform.platform(),
                            "env_digest": sha256_hex(jcs({"python": sys.version.split()[0]}).encode("utf-8"))},
        "verdicts": verdicts,
        "summary": summary,
        "digest_report": {
            "input_digest": md,
            "output_digest": sha256_hex(jcs({"verdicts": verdicts, "summary": summary}).encode("utf-8")),
            "canonicalizer_version": fx["envelope"]["payload"].get("canonicalizer_version"),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if summary["fail"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
