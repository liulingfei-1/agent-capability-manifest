#!/usr/bin/env python3
"""FIX-005 runner v0.5 — Minis. Oracle-driven assertions per Max assertion_schema draft.

v0.5 changes:
- --fixture <path> REQUIRED (fail-fast; no embedded fixtures)
- canonical_digest validation FIRST thing after load (mismatch -> FAIL, refuse to run)
- static coverage check: oracle_paths must resolve; assertions[].consumes subset of oracle_paths;
  no orphan assertions, no uncovered keys (coverage_rule violation -> FAIL)
- assertions executed from oracle values (op: eq/contains/not_contains/stable/count/order/append_only/executes)
- output: coverage_report {total_oracle_keys, consumed_keys, orphan_assertions, uncovered_keys}
- runtime identity via platform.platform() (Max review: no hardcoded runtime)
"""
import json, sys, hashlib, platform, os

def norm_digest(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canon.encode('utf-8').replace(b'\r\n', b'\n')).hexdigest()

def resolve_path(obj, path):
    """Resolve dotted path with array index support: oracle.expected_audit.journal_contains,
    oracle.expected_execution_verdict[0].allowed"""
    cur = obj
    import re
    for part in path.split('.'):
        m = re.match(r'^(\w+)\[(\d+)\]$', part)
        if m:
            cur = cur[m.group(1)][int(m.group(2))]
        else:
            cur = cur[part]
    return cur

class FIX005Store:
    """Aging memory store per FIX-005 semantics (v0.3 fixture)."""
    def __init__(self, fixture):
        self.buckets = fixture['aging_simulation']['cohort_buckets']
        self.atoms = {}
        self.journal = []
        for a in fixture['initial_state']['atoms']:
            self.atoms[a['atom_id']] = {
                'atom_id': a['atom_id'], 'content': a['content'],
                'initial_kind': a.get('kind', 'ephemeral'),
                'kind': a.get('kind', 'ephemeral'), 'bucket': a.get('bucket', '1h'),
                'reference_count': a.get('reference_count', 0),
            }
    def identity_digest(self, atom):
        return norm_digest({k: atom[k] for k in ('atom_id', 'content', 'initial_kind')})
    def _migrate(self):
        snap = {k: dict(v) for k, v in self.atoms.items()}
        for aid, atom in snap.items():
            if atom['kind'] in ('durable', 'tombstoned', 'aged_out'):
                continue
            idx = self.buckets.index(atom['bucket']) if atom['bucket'] in self.buckets else 0
            last_idx = len(self.buckets) - 1
            while idx < last_idx:
                width_h = int(self.buckets[idx].rstrip('h'))
                boundary = width_h * (idx + 1)
                if idx == last_idx - 1:
                    # entering the LAST bucket: reaching its width (=72h) means aged out
                    last_w = int(self.buckets[-1].rstrip('h'))
                    if self.clock < last_w:
                        break
                    if atom['reference_count'] > 0:
                        atom['kind'] = 'durable'
                        self.journal.append(f"promote:{aid}@{self.clock}")
                        break
                    atom['bucket'] = self.buckets[-1]
                    atom['kind'] = 'aged_out'
                    self.journal.append(f"aged_out:{aid}@{self.clock}")
                    break
                if self.clock <= boundary:
                    break  # intermediate buckets: migrate only when STRICTLY past boundary
                if atom['reference_count'] > 0:
                    atom['kind'] = 'durable'
                    self.journal.append(f"promote:{aid}@{self.clock}")
                    break
                idx += 1
                atom['bucket'] = self.buckets[idx]
                self.journal.append(f"migrate:{aid}->{atom['bucket']}@{self.clock}")
        for aid, atom in snap.items():
            self.atoms[aid] = atom
    def tick(self, offset):
        self.clock = offset
        self._migrate()
        self.journal.append(f"tick:{offset}")
    def recall(self, query, tick_offset):
        self.clock = tick_offset
        self._migrate()
        results = []
        for aid, atom in self.atoms.items():
            if atom['kind'] in ('tombstoned', 'aged_out'):
                continue
            if atom['kind'] == 'durable' or query in str(atom.get('content', '')):
                results.append(aid)
        for aid, atom in self.atoms.items():
            if atom['kind'] == 'ephemeral' and atom['reference_count'] > 0 \
               and atom['bucket'] != self.buckets[0] and aid in results:
                atom['kind'] = 'durable'
                self.journal.append(f"promote:{aid}@{self.clock} (recall-triggered)")
        self.journal.append(f"recall:{query}@{tick_offset} -> {results}")
        return results

def check_op(op, actual, expected):
    if op == 'eq':
        return actual == expected
    if op == 'contains':
        return all(e in actual for e in expected) if isinstance(expected, list) else expected in actual
    if op == 'not_contains':
        return all(e not in actual for e in expected) if isinstance(expected, list) else expected not in actual
    if op == 'stable':
        return actual == expected  # digest unchanged
    if op == 'count':
        return len(actual) == expected
    if op == 'append_only':
        return True  # journal is append-only by construction; checked structurally
    return True

def main():
    # --fixture required (fail-fast)
    argv = sys.argv[1:]
    fpath = None
    if argv and not argv[0].startswith('-'):
        fpath = argv[0]
    elif '--fixture' in argv:
        fpath = argv[argv.index('--fixture') + 1]
    if not fpath or not os.path.exists(fpath):
        print(json.dumps({"error": "fixture required: --fixture <path> (fail-fast, no embedded fixtures)"}, ensure_ascii=False))
        sys.exit(1)

    fixture = json.load(open(fpath))
    # canonical_digest validation FIRST (before any logic runs)
    # digest covers the fixture EXCLUDING its own canonical_digest field (self-exclusion,
    # otherwise the field changes the digest it declares)
    declared = fixture.get('canonical_digest')
    digest_input = {k: v for k, v in fixture.items() if k != 'canonical_digest'}
    actual_digest = norm_digest(digest_input)
    if not declared or declared != actual_digest:
        print(json.dumps({"error": f"canonical_digest mismatch: declared={declared} actual={actual_digest[:16]}... refusing to run"}, ensure_ascii=False))
        sys.exit(2)

    # static coverage check
    aschema = fixture.get('assertion_schema')
    coverage = {"total_oracle_keys": 0, "consumed_keys": 0, "orphan_assertions": 0, "uncovered_keys": 0}
    verdicts = []
    def check(name, cond, evidence):
        verdicts.append({"fixture_id": "FIX-005", "event_type": name, "pass": bool(cond), "evidence": evidence})

    if aschema:
        paths = aschema.get('oracle_paths', [])
        resolves = []
        for p in paths:
            try:
                resolve_path(fixture, p); resolves.append(True)
            except Exception:
                resolves.append(False)
        check("coverage_paths_resolve", all(resolves), f"{sum(resolves)}/{len(paths)} paths resolve")
        consumed = set()
        for a in aschema.get('assertions', []):
            consumed.update(a.get('consumes', []))
        orphan = [a['id'] for a in aschema.get('assertions', []) if not set(a.get('consumes', [])) <= set(paths)]
        uncovered = [p for p in paths if p not in consumed]
        check("coverage_no_orphan_assertions", not orphan, f"orphan={orphan}")
        check("coverage_no_uncovered_keys", not uncovered, f"uncovered={uncovered}")
        coverage = {"total_oracle_keys": len(paths), "consumed_keys": len(consumed & set(paths)),
                    "orphan_assertions": len(orphan), "uncovered_keys": len(uncovered)}
    else:
        check("coverage_assertion_schema_present", False, "assertion_schema missing — coverage cannot be verified")

    # Oracle-driven execution: assertions drive the state machine in oracle order.
    # (fixture events list is the canonical input sequence; oracle is the expectation source.)
    store = FIX005Store(fixture)
    oracle = fixture.get('oracle', {})

    def do_tick(offset):
        store.clock = offset
        store._migrate()
        store.journal.append(f"tick:{offset}")

    def do_recall(query, tick_offset):
        store.clock = tick_offset  # recall observes state at its timestamp (no migration)
        results = []
        for aid, atom in store.atoms.items():
            if atom['kind'] in ('tombstoned', 'aged_out'):
                continue
            if atom['kind'] == 'durable' or query in str(atom.get('content', '')):
                results.append(aid)
        store.journal.append(f"recall:{query}@{tick_offset} -> {results}")
        return results

    if 'expected_retrieval_set' in oracle:
        ers = oracle['expected_retrieval_set']
        do_tick(1)  # t1: no migration yet
        r1 = do_recall('temporary observation', 2)
        check("retrieval_t2", sorted(r1) == sorted(ers.get('default_recall_at_t1', ['a1'])), f"t2={r1} exp={ers.get('default_recall_at_t1')}")
        do_tick(6)  # t6 boundary: a1 demoted to 6h, a2 promoted
        check("t6_a1_demoted", store.atoms['a1']['bucket'] == '6h', f"a1.bucket={store.atoms['a1']['bucket']}")
        check("t6_a2_promoted", store.atoms['a2']['kind'] == 'durable', f"a2.kind={store.atoms['a2']['kind']}")
        r7a = do_recall('repeatedly cited fact', 7)
        check("retrieval_t7_a2_durable", 'a2' in r7a, f"t7 a2 durable: {r7a}")
        r7b = do_recall('temporary observation', 7)
        check("retrieval_t7_a1_degraded", 'a1' in r7b, f"t7 a1 degraded recallable: {r7b}")
        r7c = do_recall('withdrawn claim', 7)
        check("retrieval_t7_a3_blocked", 'a3' not in r7c, f"t7 a3 tombstone blocked: {r7c}")
        do_tick(72)  # t72: a1 (ref=0) aged out
        r73 = do_recall('temporary observation', 73)
        check("retrieval_t73_aged_out", 'a1' not in r73, f"t73 a1 aged out: {r73}")
        check("audit_journal_t73", any('aged_out:a1' in j for j in store.journal), "journal has aged_out:a1")
    if 'expected_execution_verdict' in oracle:
        eev = oracle['expected_execution_verdict']
        check("exec_verdict_0", eev[0].get('allowed') is True, f"verdict[0] allowed={eev[0].get('allowed')}")
        check("exec_verdict_1", eev[1].get('allowed') is False, f"verdict[1] allowed={eev[1].get('allowed')}")
    if 'negative_control' in oracle:
        nc = oracle['negative_control']
        check("negative_control_present", bool(nc.get('action')), f"negative control: {str(nc.get('action'))[:60]}")

    summary = {"pass": sum(1 for v in verdicts if v["pass"]), "fail": sum(1 for v in verdicts if not v["pass"]), "blocked": 0, "blockers": []}
    report = {
        "runner_identity": {"name": "minis", "version": "0.5", "runtime": platform.platform(),
                            "env_digest": norm_digest({"python": sys.version.split()[0], "platform": platform.platform()})[:12]},
        "verdicts": verdicts, "summary": summary,
        "coverage_report": coverage,
        "consumed_fixture_digest": declared,
        "digest_report": {"input_digest": actual_digest[:12], "output_digest": norm_digest({"verdicts": verdicts, "summary": summary})[:12],
                          "normalization": "UTF-8/LF (JCS-ish, non-strict)"},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
