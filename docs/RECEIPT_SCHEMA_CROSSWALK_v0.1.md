# Receipt Schema Crosswalk v0.1

> Minis × CD-4c audit-chain receipt 对照稿，面向 2026-08-17 fixture exchange。
> 目标：字段对齐，不把证据链、语义裁决、执行授权混成一个字段。

## 1. 共同不变量

1. **证据裁决 ≠ 语义主张**：`UNVERIFIED` / `INDET` 只表示当前证据不能完成验证；必须 fence execution、保留诊断材料并进入 revalidation。
2. **身份 digest ≠ 传输/文件 digest**：身份 digest 认证语义原子；fixture/input digest 认证交换字节；两者都要保留，不能互相替代。
3. **read-back proof ≠ gate verdict**：回读证明放在独立 receipt family，通过 digest reference 关联，不并入授权裁决。
4. **跨运行时先对账输入，再对账输出**：input/fixture digest 不同，不能直接比较 verdict；先分类为 `fixture_drift` / `partial_assembly` / `schema_normalization`。

## 2. 字段逐项对照

| 语义 | Minis contract v0.3 / runner report | CD-4c audit-chain receipt | 对齐规则 |
|---|---|---|---|
| 交换输入锚 | `digest_report.input_digest`（fixture canonical digest；self-excluded） | `anchor_ref` 指向输入/证据锚 | 同一输入必须字节级一致；不一致 → `UNVERIFIED` + fence |
| 语义身份锚 | `atom_id + content + initial_kind`；FIX-008 另含 `direction` | disposition/claim identity digest | 只认证语义身份，不包含 bucket/status/weight 等可变状态 |
| 审计链位置 | `digest_report.output_digest` + `verdicts[]` + trace | `row_digest_ref`（parent-linked row digest） | output digest 是报告对象锚；row digest 是行链位置；可互指但不等同 |
| 来源/fixture 证明 | `consumed_fixture_digest`、`canonical_digest` | `anchor_ref` + fixture/reference anchor | receipt 必须记录 fixture、runner、identity schema 三元组 |
| 版本冻结 | `runner_identity.version`、`canonicalizer_version`、`mapping_version` | `mapping_version`、protocol/version pin | 对拍键至少是 `{fixture_digest, runner_version, identity_schema_version}` |
| 期望值 | fixture `oracle.expected_*` | oracle/disposition expected path | 期望值只从 oracle 读取，不能硬编码进 runner |
| 实际值 | runner `verdicts[]`、`trace`、`observations` | receipt actual / disposition trace | 必须保留 expected vs actual，不只输出 PASS/FAIL |
| 分歧 | `divergence`（矩阵公共断言 + expected/actual） | `divergence` | 最小字段：`path`, `expected`, `actual`, `failure_class` |
| 证据状态 | `PASS` / `FAIL` / `UNVERIFIED` / `UNCLASSIFIED` | `PASS` / `INDET` / `FAIL` / `UNKNOWN` / `MISALIGNED`（对方实现可扩展） | 单向映射：PASS↔PASS，FAIL↔FAIL，UNVERIFIED↔INDET，未跑↔UNKNOWN，范围外↔UNCLASSIFIED/MISALIGNED |
| 执行处置 | `ACTIVE` / `REJECT` / `HOLD+fence` | gate/disposition（如 `GATE_DENIED` / `UNBOUNDED`） | `UNVERIFIED` 不得降级成语义 FAIL；处置层单独记录 fence |
| epoch | `epoch` / `execution_epoch`（FIX-006 trace/authority） | `epoch_context.fence_epoch` | 必须绑定 receipt；epoch 不同不得声称同一运行结果 |
| 策略版本 | `policy_version`（重评估键） | policy/mapping version | register/policy 变化走版本重评估，不逐原子伪造撤回 |
| 重放锚 | `trace` + `replay_seed` | `replay_seed` + parent row digest | 重放先验证链，再比较 verdict；旧链头必须 REJECT |

## 3. 推荐的规范化 receipt envelope

```json
{
  "receipt_schema": "cross-runtime-receipt/v0.1",
  "fixture_digest": "<64 lowercase hex>",
  "runner_version": "<semver or pinned implementation version>",
  "identity_schema_version": "<version>",
  "input_digest": "<64 lowercase hex>",
  "expected": {"oracle_path": "<path>", "value": "<oracle value>"},
  "actual": {"value": "<observed value>", "evidence_ref": "<digest-ref>"},
  "divergence": null,
  "epoch": "<fence epoch>",
  "policy_version": "<policy version>",
  "evidence_state": "PASS",
  "operational_disposition": "ACTIVE",
  "row_digest_ref": "<optional parent-linked audit row>",
  "anchor_ref": "<optional signed source/set-root anchor>",
  "mapping_version": "7",
  "replay_seed": "<deterministic seed>"
}
```

## 4. Divergence classification

| failure_class | 触发 | 处置 |
|---|---|---|
| `fixture_drift` | 同名 fixture 原始/规范化字节不同 | UNVERIFIED + fence |
| `partial_assembly` | 漏掉 manifest/events/oracle/cross-runtime 必需节 | UNVERIFIED + reject execution |
| `runner_skew` | 同输入但断言/状态机逻辑不同 | UNVERIFIED + runner review |
| `schema_normalization` | JCS/NFC/编码/换行规则不同 | UNVERIFIED + canonicalizer review |
| `authority_epoch_mismatch` | set-root/执行锚 epoch 不匹配 | UNVERIFIED + REVALIDATION_PENDING |
| `oracle_divergence` | 输入一致但 actual 与 oracle 不一致 | FAIL（若语义已确定）或 UNVERIFIED（证据不足） |

## 5. Byte-level swap protocol

1. 固定公开 commit 与文件原始 SHA-256。
2. 独立 clone 到隔离目录；静态检查 runner，确认不执行 fixture 内代码。
3. 重算 `fixture_digest` / `input_digest`，不一致时停止，不比较 output。
4. 运行 runner，保存完整 JSON report，不截断 digest。
5. 先比较 row/trace 链，再按公共断言路径比较 expected/actual。
6. 任何 `UNVERIFIED` 保留诊断材料，不升级为 PASS 或 FAIL；完成 revalidation 后再提交新 receipt。

---
*Minis × CD-4c audit-chain crosswalk v0.1 · 2026-08-12*