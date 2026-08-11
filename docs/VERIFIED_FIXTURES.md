# VERIFIED FIXTURES — 对拍基准锚（2026-08-11）

> 目的：固定各 fixture/runner 版本 + canonical digest，作为跨运行时/跨实现对拍的统一基准（凯瑞建议）
> 仓库：github.com/liulingfei-1/agent-capability-manifest（main 分支）

| Fixture | 版本 | Runner | canonical digest | 预期 verdict | 验证状态 |
|---|---|---|---|---|---|
| FIX-005 | v0.4 | fix005_runner.py v0.5 | 8cd161245579bd42 | 14/14 PASS | 已验证 |
| FIX-006 | v0.2-locked | fix006_runner.py v0.4 | b4c0243aeb014326 | 12/12 PASS | 已验证 |
| FIX-007 | v0.2 | fix007_runner.py v0.3 | 4126aa999c7026b4 | 17/17 PASS | 已验证 |
| FIX-L3-001 | v0.1 | fixl3_runner.py v0.1 | f529f9a9433f508d | PASS | 已验证 |
| FIX-L3-002 | v0.1 | fixl3_runner.py v0.1 | d73d973e0330e546 | FAIL (evidence_anchor_mismatch) | 已验证 |
| FIX-L3-003 | v0.1 | fixl3_runner.py v0.1 | 9bca36390437d045 | FAIL (oracle_coverage_gap) | 已验证 |
| FIX-L3-004 | v0.1 | fixl3_runner.py v0.1 | 62753411b28cdc92 | FAIL (fixture_digest_mismatch) | 已验证 |
| FIX-L3-005 | v0.1 | fixl3_runner.py v0.1 | bb7e2e2a11869ff2 | UNVERIFIED (canonicalizer_version_mismatch) | 已验证 |
| FIX-L3-006 | v0.1 | fixl3_runner.py v0.1 | 2e388305d3a57ce8 | MIGRATED_PASS | 已验证 |

## 说明

- canonical digest = self-excluded（排除 canonical_digest 与 evidence_anchor.fixture_digest 循环引用对）
- runner 均为零依赖 Python 3.8+，输出 digest_report 绑定 input/output digest
- FIX-L3-002 修复版（commit a499eaba76）：单义负控，只测 evidence_anchor_mismatch

---
*Minis · 2026-08-11，凯瑞建议产出*
