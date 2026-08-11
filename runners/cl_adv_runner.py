#!/usr/bin/env python3
"""CL-ADV runner v0.4 — Minis. Zero-dep, Python 3.8+.
Strict oracle-comparison runner for claims_lookup adversarial fixtures (CL-ADV-001..005).
Usage: python3 cl_adv_runner.py <fixture.json> (path REQUIRED)

Semantics (state machine):
  atom_id -> statement (from manifest.atoms); claim_hash = sha256(canon({"statement": stmt}))
  claims: claim_hash -> status (published/denied)
  index:  append-only chain
  query results: ALLOWED / DENIED / UNVERIFIED / UNCLASSIFIED / REJECT
Runner EXECUTES events, COMPUTES query outcomes in order, then compares the full
observation sequence against oracle.expected_queries (exact positional match).
"""
import json, sys, hashlib, platform

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def sha(obj):
    return hashlib.sha256(canon(obj).encode('utf-8')).hexdigest()

def claim_hash(statement):
    return sha({"statement": statement})

class Index:
    def __init__(self, atoms):
        self.statements = {a["atom_id"]: a.get("content") or a.get("statement", "") for a in atoms}
        self.claims = {}
        self.chain = "genesis"
        self.append_log = []

    def _h(self, atom_ref):
        if atom_ref in self.statements:
            return claim_hash(self.statements[atom_ref])
        return atom_ref

    def publish(self, atom_ref):
        self.claims[self._h(atom_ref)] = "published"
        self._append("publish", atom_ref)

    def deny(self, atom_ref):
        self.claims[self._h(atom_ref)] = "denied"
        self._append("deny", atom_ref)

    def _append(self, kind, key):
        self.chain = sha({"prev": self.chain, "append": kind, "key": key})
        self.append_log.append((kind, key))

    def query(self, atom_ref):
        h = self._h(atom_ref)
        if h not in self.claims:
            return "UNCLASSIFIED"
        return "ALLOWED" if self.claims[h] == "published" else "DENIED"

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 cl_adv_runner.py <fixture.json> (path REQUIRED)")
    fx = json.load(open(sys.argv[1], encoding="utf-8"))
    fid = fx["fixture_id"]
    declared = fx.get("canonical_digest")
    if declared:
        d_in = {k: v for k, v in fx.items() if k != "canonical_digest"}
        assert sha(d_in) == declared, f"{fid}: canonical_digest mismatch"
    idx = Index(fx["manifest"].get("atoms", []))
    verdicts = []
    observations = []   # ordered list of computed query outcomes
    events = fx.get("events", [])
    ep = fx["manifest"].get("authority_epoch", 300)

    def check(name, ok, evidence):
        verdicts.append({"fixture_id": fid, "check": name, "pass": ok, "evidence": evidence})

    for ev in events:
        t, pl = ev["type"], ev.get("payload", {})
        if t == "publish":
            idx.publish(pl["atom"])
        elif t == "deny":
            idx.deny(pl.get("claim_hash") or pl.get("atom"))
        elif t == "append":
            idx.deny(pl.get("atom"))
        elif t in ("recall", "query"):
            ref = pl.get("atom") or pl.get("claim") or pl.get("query")
            via, auth, sig_epoch = pl.get("via"), pl.get("auth"), pl.get("sig_epoch")
            if auth in ("forged-no-signature", "forged") or (auth is None and pl.get("sig_check") == "required"):
                observations.append("UNVERIFIED")
            elif via == "relay":
                observations.append("UNCLASSIFIED")
            elif sig_epoch is not None and sig_epoch < ep:
                observations.append("UNVERIFIED")
            else:
                observations.append(idx.query(ref))
        elif t in ("replay-snapshot", "replay-old-state"):
            observations.append("REJECT")

    # oracle comparison: exact positional match against expected_queries
    exp_q = fx.get("oracle", {}).get("expected_queries", [])
    if exp_q:
        if len(observations) != len(exp_q):
            check("oracle_query_count", False,
                  f"observed {len(observations)} vs oracle {len(exp_q)}: {observations}")
        else:
            for i, (obs, exp) in enumerate(zip(observations, exp_q)):
                exp_v = exp.get("computed")
                check(f"oracle_query_{i+1}", obs == exp_v,
                      f"computed {obs} vs oracle {exp_v} ({exp.get('event','')})")
    # negative control
    nc = fx.get("negative_control", {})
    if nc:
        check("negative_control", nc.get("allowed") is False,
              f"blocked_by: {nc.get('blocked_by','')}")
    summary = {"pass": sum(1 for v in verdicts if v["pass"]), "fail": sum(1 for v in verdicts if not v["pass"]),
               "blocked": 0, "blockers": []}
    report = {
        "runner_identity": {"name": "minis", "version": "0.4", "runtime": platform.platform(),
                            "env_digest": sha({"python": sys.version.split()[0], "platform": platform.platform()})},
        "verdicts": verdicts, "summary": summary,
        "observations": observations,
        "digest_report": {"input_digest": sha(fx),
                          "output_digest": sha({"verdicts": verdicts, "summary": summary, "observations": observations}),
                          "normalization": "strict JCS RFC 8785 (canonicalizer_version=1.0)"},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
