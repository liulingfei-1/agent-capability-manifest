# VERIFIED FIXTURES — 对拍基准锚 v0.2（2026-08-11）

> 目的：固定 fixture/runner 版本 + canonical digest + canonicalization 规则，作为跨运行时/跨实现对拍的统一基准
> 仓库：github.com/liulingfei-1/agent-capability-manifest（main 分支）

## canonicalization 规则（统一）

- canonicalizer_version = **1.0（严格 JCS RFC 8785）**，对齐 CD-4c canonicalizer 6c3158e
- UTF-8 / LF / NFC mandatory / 无终止换行 / sort_keys compact / canonical_digest 与 evidence_anchor.fixture_digest 自排除
- **禁止跨 profile 混比**（canonicalizer_version 必须一致）

## Fixture 基准表

| 配对键 | Fixture | 版本 | Runner（实现方）| canonical digest（完整 64 位）| evidence verdict | operational disposition |
|---|---|---|---|---|---|---|
| minis:FIX-005 | FIX-005 | v0.4 | fix005_runner.py v0.6 (minis) | 8cd161245579bd42f9b7f121d5723acd2b553da9c1c4f20db772907763f8ade2 | PASS | ACTIVE |
| minis:FIX-006 | FIX-006 | v0.2-locked | fix006_runner.py v0.6 (minis) | 40efe29f2235709d57b00664857467d08cac0575ac2f0e5e802b526ee1442716 | PASS | ACTIVE |
| minis:CD4C-E4 | CD4C-E4 | v0.1-byteform | cd4c_toctou_runner.py v0.2 (minis) | aef61dd48b6af596b81a794b0a951def87f732a12a6a0664f5ccbd6d5948aa1d | PASS | ACTIVE |
| minis:CD4C-E5 | CD4C-E5 | v0.1-byteform | cd4c_toctou_runner.py v0.2 (minis) | 09608d895bf5032460fd77a47287ffe6a86361b70e1b7ab60440043d9e4d57f7 | PASS | ACTIVE |
| minis:FIX-007 | FIX-007 | v0.2 | fix007_runner.py v0.3 (minis) | 4126aa999c7026b4d42ab2e79d2075c3bf1d937e362a027a7e189672c0aa64cf | PASS | ACTIVE |
| minis:FIX-L3-001 | FIX-L3-001 | v0.1 | fixl3_runner.py v0.1 (minis) | f529f9a9433f508d43a9184a80a19a1d3730fe704567bb14af20e831acbd0745 | PASS | ACTIVE |
| minis:FIX-L3-002 | FIX-L3-002 | v0.1 | fixl3_runner.py v0.1 (minis) | d73d973e0330e5468609b412c5a539f800a014cea1f29438304da23e6ad8be63 | FAIL (evidence_anchor_mismatch) | REJECT |
| minis:FIX-L3-003 | FIX-L3-003 | v0.1 | fixl3_runner.py v0.1 (minis) | 9bca36390437d0452beb51011312dfcd754ee706e84943c5af53368c728dbac4 | FAIL (oracle_coverage_gap) | REJECT |
| minis:FIX-L3-004 | FIX-L3-004 | v0.1 | fixl3_runner.py v0.1 (minis) | 62753411b28cdc92689328887c8cb66a959e1f4542a2f9d3cb496183b5211f64 | FAIL (fixture_digest_mismatch) | REJECT |
| minis:FIX-L3-005 | FIX-L3-005 | v0.1 | fixl3_runner.py v0.1 (minis) | bb7e2e2a11869ff23c5cb91b96d8e9c71620672407b98409fc53800cfaa19c0e | UNVERIFIED | HOLD/fence |
| minis:FIX-L3-006 | FIX-L3-006 | v0.1 | fixl3_runner.py v0.1 (minis) | 2e388305d3a57ce8e8cd2702fc2f82214b19fdc0c51ecd4bbc4e7f3a15d630e9 | MIGRATED_PASS | ACTIVE |
| huaahua:FIX-005 | FIX-005 | v0.3 | verify.py (huaahua-cd4c) | d73e84c3ceb678513187ddc8515db7da8b4a8d29d9a2ff28e3dd4d89a2069fe6 | PASS | ACTIVE |
| huaahua:FIX-006 | FIX-006 | v0.2-locked | verify.py (huaahua-cd4c) | 40efe29f2235709d57b00664857467d08cac0575ac2f0e5e802b526ee1442716 | PASS | ACTIVE |
| max:FIX-005 | FIX-005 | v0.3 | fix005_runner.py v0.3 (max-win) | e95e2cdb00b7e046fb5d8648a2b776a49c3ec2981ec8f0b276251bc29401b5b9 | PASS | ACTIVE |
| max:FIX-006 | FIX-006 | v0.2-locked | fix006_runner.py v0.6 (max-win) | 40efe29f2235709d57b00664857467d08cac0575ac2f0e5e802b526ee1442716 | PASS | ACTIVE |

## 生成工具

- Python 3.12.13 + hashlib（sha256）+ 严格 JCS RFC 8785 序列化器（canonicalizer_version=1.0）
- 展示可缩短为 16 位前缀，对拍/核验必须用完整 64 位（防截断或 canonicalizer 漂移误判）

## 说明

- **配对键** = runner_identity:fixture_id——同名 fixture 不同 runner 用配对键区分（避免歧义）
- **evidence verdict** = 证据裁决（PASS/FAIL/UNVERIFIED/MIGRATED_PASS）
- **operational disposition** = 操作处置（ACTIVE/REJECT/HOLD+fence）——UNVERIFIED 证据状态对应 HOLD/fence 处置（凯瑞拆分建议）
- 跨实现对拍：同配对键 + 同 canonicalizer_version 下比 digest

## CD4C-E4/E5 补充说明（2026-08-14）

- CD4C-E4/E5 按 docs/fixture-interchange-spec.md 对齐：cd4c-fixture-v1 envelope、6 字段行格式、`row_digest=SHA256(parent_ascii ‖ JCS(row))`、canonicalizer_version=1
- E4 含 masked-replay 负控（同 epoch 序号 intent 变化 → FAIL）；E5 含三轴偏序负控（read>admit、admit>receipt → FAIL）
- 官方 CD-4c tools/verify.py 复验：双 ALL ROWS VERIFIED；本地 runner E4 7/7、E5 6/6
- 已提 PR #3（fixtures/cd4c/Minis-E4-epoch-monotonic-sequence.json + Minis-E5-three-epoch-partial-order.json），8/17 对拍交付

---
*Minis · 2026-08-14 v0.3，E4/E5 基准锚 + 凯瑞细化建议落地*
