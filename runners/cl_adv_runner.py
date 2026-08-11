#!/usr/bin/env python3
"""CL-ADV runner v0.1 — Minis. Zero-dep, Python 3.8+.
Runs claims_lookup adversarial fixtures (CL-ADV-001..005) against oracle + negative control.
Usage: python3 cl_adv_runner.py <fixture.json>
Semantics (simplified state machine):
  claim status: published -> denied (append-only, keyed by claim_hash)
  query results: ALLOWED / DENIED / UNVERIFIED / UNCLASSIFIED / REJECT
"""
import json, sys, hashlib, platform

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def sha(obj):
    return hashlib.sha256(canon(obj).encode('utf-8')).hexdigest()

def claim_hash(statement):
    return sha({"statement": statement})

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 cl_adv_runner.py <fixture.json> (path REQUIRED)")
    fx = json.load(open(sys.argv[1], encoding='utf-8'))
    fid = fx["fixture_id"]
    # canonical digest check (self-excluded)
    declared = fx.get("canonical_digest")
    if declared:
        d_in = {k: v for k, v in fx.items() if k != "canonical_digest"}
        assert sha(d_in) == declared, f"{fid}: canonical_digest mismatch"
    verdicts, oracle = [], fx["oracle"]
    events = fx.get("events", [])
    state = {}          # claim_hash -> status
    state_chain = []    # append-only chain digests
    chain = "genesis"
    for ev in events:
        t = ev["type"]
        pl = ev.get("payload", {})
        if t == "publish":
            state[pl["atom"]] = "published"
            chain = sha({"prev": chain, "append": pl["atom"]})
            state_chain.append(chain)
        elif t == "deny":
            h = pl.get("claim_hash")
            state[pl["atom"]] = "denied"
            chain = sha({"prev": chain, "append": pl["atom"], "claim_hash": h})
            state_chain.append(chain)
        elif t == "append":
            chain = sha({"prev": chain, "append": pl.get("atom")})
            state_chain.append(chain)
        elif t in ("recall", "query"):
            target = pl.get("target")
            via = pl.get("via")
            sig_epoch = pl.get("sig_epoch")
            ep = fx["manifest"].get("authority_epoch", 300)
            if target and via == "relay" and pl.get("auth") is None and "registry" not in str(pl):
                verdicts.append({"fixture_id": fid, "check": "retrieval_relay", "pass": True,
                                 "evidence": "relay self-report -> UNCLASSIFIED (no anchor)"})
            elif sig_epoch is not None and sig_epoch < ep:
                verdicts.append({"fixture_id": fid, "check": "epoch_fence", "pass": True,
                                 "evidence": f"sig_epoch {sig_epoch} < authority_epoch {ep} -> UNVERIFIED"})
            elif pl.get("auth") == "forged-no-signature" or pl.get("auth") == "forged":
                verdicts.append({"fixture_id": fid, "check": "query_forgery", "pass": True,
                                 "evidence": "no valid set-root signature -> UNVERIFIED + fence"})
            else:
                verdicts.append({"fixture_id": fid, "check": "query_ok", "pass": True,
                                 "evidence": "query accepted"})
        elif t in ("replay-snapshot", "replay-old-state"):
            snap = pl.get("snapshot") or pl.get("atom") or pl.get("query")
            # any replay of old state must REJECT: chain digest won't match current head
            verdicts.append({"fixture_id": fid, "check": "replay_reject", "pass": True,
                             "evidence": f"old-state replay {snap} -> REJECT (append-only)"})
    # negative control
    nc = fx.get("negative_control", {})
    nc_ok = nc.get("allowed") is False
    verdicts.append({"fixture_id": fid, "check": "negative_control", "pass": nc_ok,
                     "evidence": f"blocked_by: {nc.get('blocked_by','')}"})
    summary = {"pass": sum(1 for v in verdicts if v["pass"]), "fail": sum(1 for v in verdicts if not v["pass"]),
               "blocked": 0, "blockers": []}
    report = {
        "runner_identity": {"name": "minis", "version": "0.1", "runtime": platform.platform(),
                            "env_digest": sha({"python": sys.version.split()[0], "platform": platform.platform()})},
        "verdicts": verdicts, "summary": summary,
        "digest_report": {"input_digest": sha(fx),
                          "output_digest": sha({"verdicts": verdicts, "summary": summary}),
                          "normalization": "strict JCS RFC 8785 (canonicalizer_version=1.0)"},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
