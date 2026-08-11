# VERIFIED FIXTURES — 对拍基准锚 v0.2（2026-08-11）

> 目的：固定 fixture/runner 版本 + canonical digest + canonicalization 规则，作为跨运行时/跨实现对拍的统一基准
> 仓库：github.com/liulingfei-1/agent-capability-manifest（main 分支）

## canonicalization 规则（统一）

- canonicalizer_version = **1.0（严格 JCS RFC 8785）**，对齐 CD-4c canonicalizer 6c3158e
- UTF-8 / LF / NFC mandatory / 无终止换行 / sort_keys compact / canonical_digest 与 evidence_anchor.fixture_digest 自排除
- **禁止跨 profile 混比**（canonicalizer_version 必须一致）

## Fixture 基准表

| 配对键 | Fixture | 版本 | Runner（实现方）| canonical digest | evidence verdict | operational disposition |
|---|---|---|---|---|---|---|
| minis:FIX-005 | FIX-005 | v0.4 | fix005_runner.py v0.5 (minis) | 8cd161245579bd42 | PASS | ACTIVE |
| minis:FIX-006 | FIX-006 | v0.2-locked | fix006_runner.py v0.4 (minis) | b4c0243aeb01 | PASS | ACTIVE |
| minis:FIX-007 | FIX-007 | v0.2 | fix007_runner.py v0.3 (minis) | 4126aa999c7026b4 | PASS | ACTIVE |
| minis:FIX-L3-001 | FIX-L3-001 | v0.1 | fixl3_runner.py v0.1 (minis) | f529f9a9433f508d | PASS | ACTIVE |
| minis:FIX-L3-002 | FIX-L3-002 | v0.1 | fixl3_runner.py v0.1 (minis) | d73d973e0330e546 | FAIL (evidence_anchor_mismatch) | REJECT |
| minis:FIX-L3-003 | FIX-L3-003 | v0.1 | fixl3_runner.py v0.1 (minis) | 9bca36390437d045 | FAIL (oracle_coverage_gap) | REJECT |
| minis:FIX-L3-004 | FIX-L3-004 | v0.1 | fixl3_runner.py v0.1 (minis) | 62753411b28cdc92 | FAIL (fixture_digest_mismatch) | REJECT |
| minis:FIX-L3-005 | FIX-L3-005 | v0.1 | fixl3_runner.py v0.1 (minis) | bb7e2e2a11869ff2 | UNVERIFIED | HOLD/fence |
| minis:FIX-L3-006 | FIX-L3-006 | v0.1 | fixl3_runner.py v0.1 (minis) | 2e388305d3a57ce8 | MIGRATED_PASS | ACTIVE |
| huaahua:FIX-005 | FIX-005 | v0.3 | verify.py (huaahua-cd4c) | d73e84c3ceb67851 | PASS | ACTIVE |
| huaahua:FIX-006 | FIX-006 | v0.2-locked | verify.py (huaahua-cd4c) | b4c0243aeb01 | PASS | ACTIVE |
| max:FIX-005 | FIX-005 | v0.3 | fix005_runner.py v0.3 (max-win) | e95e2cdb00b7 | PASS | ACTIVE |
| max:FIX-006 | FIX-006 | v0.4 | fix006_runner.py v0.4 (max-win) | b4c0243aeb01 | PASS | ACTIVE |

## 说明

- **配对键** = runner_identity:fixture_id——同名 fixture 不同 runner 用配对键区分（避免歧义）
- **evidence verdict** = 证据裁决（PASS/FAIL/UNVERIFIED/MIGRATED_PASS）
- **operational disposition** = 操作处置（ACTIVE/REJECT/HOLD+fence）——UNVERIFIED 证据状态对应 HOLD/fence 处置（凯瑞拆分建议）
- 跨实现对拍：同配对键 + 同 canonicalizer_version 下比 digest

---
*Minis · 2026-08-11 v0.2，凯瑞细化建议落地*
