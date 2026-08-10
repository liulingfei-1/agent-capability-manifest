#!/usr/bin/env python3
"""FIX-006 runner v0.4 — Minis. EXTERNALIZED fixtures (Max review: hardcoded fixtures
break cross-runtime comparison premise). Reads fixture JSON file, runs main scenario
(manifest.events) + all negative_controls, asserts oracle per scenario.

Portable: no paths, no deps, Python 3.8+. Usage: python3 fix006_runner.py FIX-006.json
"""
import json, sys, hashlib

def norm_digest(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()

def short(d):
    return d[:12]

class Atom:
    def __init__(self, aid, content, initial_kind='ephemeral', ref_count=0, bucket='1h'):
        self.id = aid
        self.content = content
        self.initial_kind = initial_kind
        self.ref_count = ref_count
        self.bucket = bucket
        self.kind = initial_kind
        self.promote_events = 0
        self.audit = []

    def identity_digest(self):
        return norm_digest({'atom_id': self.id, 'content': self.content, 'initial_kind': self.initial_kind})

    def aged(self):
        return self.bucket != '1h'

BUCKETS = ['1h', '6h', '24h', '72h']

def run_scenario(name, events, exp, atoms_init):
    atoms = {}
    for a in atoms_init:
        atoms[a['atom_id']] = Atom(a['atom_id'], a.get('content', ''), a.get('kind', 'ephemeral'),
                                   a.get('reference_count', 0), a.get('bucket', '1h'))
    ordered = sorted(events, key=lambda e: int(e['tick'].rstrip('ms').lstrip('+') or 0))
    for ev in ordered:
        t = ev['type']
        if t == 'admit':
            continue  # atoms pre-seeded from manifest
        elif t == 'reference':
            a = atoms[ev['atom']]
            a.ref_count += 1
            a.audit.append(f"reference@{ev['tick']} (ref={a.ref_count})")
            if a.kind == 'ephemeral' and a.aged() and a.ref_count > 0:
                a.kind = 'durable'
                a.promote_events += 1
                a.audit.append(f"reference@{ev['tick']} -> PROMOTED (aged + ref>0)")
        elif t == 'aging_tick':
            a = atoms[ev['atom']]
            if a.kind != 'ephemeral':
                continue
            if a.ref_count > 0:
                a.kind = 'durable'
                a.promote_events += 1
                a.audit.append(f"aging_tick@{ev['tick']} -> PROMOTED (ref>0 at boundary)")
            else:
                idx = BUCKETS.index(a.bucket)
                if idx < len(BUCKETS) - 1:
                    a.bucket = BUCKETS[idx + 1]
                    a.audit.append(f"aging_tick@{ev['tick']} -> AGED to {a.bucket}")
        elif t == 'promote':
            a = atoms[ev['atom']]
            if a.kind == 'durable':
                a.audit.append(f"promote@{ev['tick']} -> NO-OP (idempotent)")
            else:
                a.kind = 'durable'
                a.promote_events += 1
                a.audit.append(f"promote@{ev['tick']} -> promoted")

    a = atoms.get('A')
    if a is None:
        return [{"pass": False, "evidence": f"{name}: atom A missing"}]

    exp_status = exp.get('A_status', 'durable')
    status_ok = (a.kind == 'durable' and exp_status in ('durable', 'promoted_to_durable', 'promoted_after_aging'))
    if exp_status == 'promoted_after_aging':
        aged_idx = next((i for i, x in enumerate(a.audit) if 'AGED' in x), None)
        prom_idx = next((i for i, x in enumerate(a.audit) if 'PROMOTED' in x), None)
        status_ok = status_ok and aged_idx is not None and prom_idx is not None and aged_idx < prom_idx
        ev_extra = f"audit order: aged@{aged_idx} < promoted@{prom_idx}"
    elif exp_status == 'promoted_to_durable':
        status_ok = status_ok and any('PROMOTED' in x for x in a.audit)
        ev_extra = "promote event present"
    else:
        ev_extra = ""
    id_ok = (a.id == 'A') and (a.identity_digest() == norm_digest({'atom_id': 'A', 'content': 'boundary-probe', 'initial_kind': 'ephemeral'}))
    count_ok = True
    if 'promote_events' in exp:
        count_ok = a.promote_events == exp['promote_events']
    if exp.get('aging_during_promotion') == 'BLOCKED':
        prom_idx = next((i for i, x in enumerate(a.audit) if 'PROMOTED' in x), None)
        aged_after = any('AGED' in x and i > (prom_idx or 0) for i, x in enumerate(a.audit))
        count_ok = count_ok and not aged_after
        ev_extra += " | BLOCKED consumed (no AGED after PROMOTED)"

    checks = [
        ("status_exact", status_ok, f"kind={a.kind} expected={exp_status} {ev_extra}"),
        ("identity_digest", id_ok, f"id={a.id} digest={short(a.identity_digest())}"),
        ("promote_count", count_ok, f"promote_events={a.promote_events}"),
    ]
    return [{"fixture_id": "FIX-006", "scenario": name, "check": cname, "pass": ok,
             "evidence": note, "full_digest": short(norm_digest({"scenario": name, "check": cname, "pass": ok}))}
            for cname, ok, note in checks]

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '/var/minis/workspace/regression-pack/FIX-006_promote_after_aging_boundary.json'
    fixture = json.load(open(path))
    input_digest = norm_digest(fixture)
    atoms_init = fixture['manifest']['atoms']
    all_v = []
    # main scenario from manifest.events
    all_v.extend(run_scenario("main", fixture['manifest'].get('events', []), fixture['manifest']['oracle']['expected'], atoms_init))
    # negative controls
    for nc in fixture.get('negative_controls', []):
        all_v.extend(run_scenario(nc['id'], nc['events'], nc['expected'], atoms_init))
    summary = {"pass": sum(1 for v in all_v if v["pass"]), "fail": sum(1 for v in all_v if not v["pass"]), "blocked": 0, "blockers": []}
    report = {
        "runner_identity": {"name": "minis", "version": "0.4", "runtime": "iSH Alpine aarch64",
                            "env_digest": short(norm_digest({"python": sys.version.split()[0]}))},
        "verdicts": all_v, "summary": summary,
        "digest_report": {"input_digest": short(input_digest), "output_digest": short(norm_digest({"verdicts": all_v, "summary": summary})),
                          "normalization": "UTF-8/LF (JCS-ish, non-strict)"},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
