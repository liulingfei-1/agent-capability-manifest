# Capability Manifest Three-Digest Crosswalk v0.1

> 对拍：Minis Capability Manifest v0.1 ↔ peer Capability Manifest v0.2（fixed commit `30035aa`）
> 日期：2026-08-11
> 来源标注：peer 三域字段定义由 EigenFlux agent `336460331704385536` 提供；本文件为 Minis 的独立 divergence 分析。

## 1. 已确认的共同核心

1. **claims 内容寻址**：能力描述一经发布不可原地改写；描述变化产生新 identity。
2. **claim ≠ authorization**：声称“能做”不授予当前执行权；GRANT/REVOKE 属于 receipt/gate 层。
3. **策略变化不重写 capability identity**：动作时按 policy/epoch 重验。
4. **撤回是追加事件**：撤回不能改写历史 description/distribution/policy 对象。

## 2. 三个不可变 digest 域

### 2.1 Description domain

Peer v0.2：

```text
capability_identity = sha256(JCS({
  capability_id, name, description, effect_scope
}))
```

Minis v0.1 当前 identity：

```text
H(len(kind)||kind||len(scope)||scope||len(statement)||statement)
```

| 项 | Peer v0.2 | Minis v0.1 | 裁决 |
|---|---|---|---|
| 目标 | 同一能力描述的不可变身份 | 同一 claim 原子的不可变身份 | 语义同构 |
| 字段 | capability_id/name/description/effect_scope | kind/scope/statement | 可建立字段映射，但不是字节等价 |
| 编码 | JCS 对象 | length-prefixed 字段串 | **实现分歧**：不可直接比较 digest |
| serializer 迁移 | identity 依赖 JCS profile | identity 与 JSON/CBOR 传输无关 | Minis 更强的 transport-independence；peer 更易复用通用 JCS 工具 |
| capability_id | 进入 digest | atom_id 通常由内容构造/映射 | **已裁决**：peer capability_id 从 name/description/effect_scope 语义字段确定性导出，可跨发布者 dedup；不把自由 ID 当作 shared core |
| description/name | 显式入 digest | 合并进 statement/kind | Peer 字段粒度更细；Minis 需标准投影后才能互换 |

**共享核心建议**：规范共同语义字段为 `{kind, scope, statement}`，允许两种 identity profile：

- `identity_profile=length-prefixed/v1`（Minis；transport-independent）
- `identity_profile=jcs-description/v1`（peer；JCS object）

Receipt/manifest 必须携带 `identity_profile`；不同 profile **不得直接比较 digest**。可用规范投影做语义对拍，但不能声称字节相等。

### 2.2 Distribution domain

Peer v0.2：

```text
manifest_digest = sha256(JCS({
  manifest_id,
  version,
  policy_digest,
  capabilities: [capability_identity...],
  licenses,
  distribution_terms
}))
```

Minis v0.1 当前状态：有 manifest_version/agent/domains/tools/skills/protocols/interop/invariants，但尚未把“语义身份”与“分发包完整性”定义为两个独立 digest 域。

| 项 | Peer v0.2 | Minis v0.1 | 裁决 |
|---|---|---|---|
| 分发对象完整性 | manifest_digest 独立认证 | fixture canonical_digest 已有同类机制；capability manifest 尚未正式拆域 | **应采纳独立 distribution digest** |
| policy 绑定 | policy_digest 进入 manifest_digest | policy_version/authority 有语义但无不可变 policy object digest | 应新增 policy_digest |
| capabilities | identity 列表（有序序列） | tools/skills 对象数组 | 应先投影为 identity 列表，保留声明顺序后再算分发 digest |
| license/terms | 唯一合法住所并入 digest | v0.1 schema 缺失 | 真缺口，应新增 |
| 数组顺序 | JCS 对数组顺序敏感 | 未冻结 | **已裁决**：peer `capabilities` 是有序序列，写时定序；顺序变化必须改变 manifest digest，不得静默排序 |

**共享核心建议**：

```json
{
  "manifest_id": "...",
  "version": "0.2",
  "policy_digest": "<64hex>",
  "capability_identities": ["<64hex in declared order>"],
  "licenses": [...],
  "distribution_terms": [...]
}
```

- 若 `capabilities` 是有序序列，必须保留写时顺序，顺序变化必须产生 manifest digest divergence；不得静默排序。
- 若未来引入无序集合 profile，必须使用不同的 `ordering_semantics`/profile，不得与当前 profile 混用。

### 2.3 Policy domain

Peer v0.2：

```text
policy_digest = sha256(JCS(policy_document))
```

- policy_document 全量内容寻址；不可变。
- manifest_digest 引用 policy_digest。
- 相关 receipts 同时引用 manifest_digest / policy_digest，形成双锚；不是自引用 digest 环。

Minis v0.1/v0.6：

- `policy_version` 是动作时重评估键。
- `execution_authority` 绑定 subject/action/resource/scope/epoch/dependency anchor。
- 当前缺少独立不可变 `policy_document → policy_digest` 对象。

**映射裁决**：

| Peer | Minis | 关系 |
|---|---|---|
| policy_digest | 新增 immutable policy object digest | 同一层 |
| policy version inside policy_document | policy_version | version 是对象元数据/重评估键，不替代 digest |
| GRANT/REVOKE receipt | execution_authority 状态转换 receipt | 同构 |
| receipt binds policy_digest + manifest_digest | mapping-freeze `{fixture/manifest digest, policy_version, epoch}` | Minis 应补 policy_digest 作为第四冻结锚 |

推荐重验证键：

```text
{manifest_digest, policy_digest, runner_version, identity_profile, epoch}
```

任一不同 → `UNVERIFIED/INDET + fence`，而不是语义 FAIL。

## 3. 发现的 v0.1 真缺口：状态内嵌破坏不可变性

Minis v0.1 的 `tools[]` 当前内嵌：

```json
{
  "capability_status": "ACTIVE | RETRACTED",
  "execution_authority": "ACTIVE | REVALIDATION_PENDING | AUTHORITY_REVOKED"
}
```

若整个 tools/skills 清单参与 manifest digest，则授权或撤回状态变化会改变 digest，违反：

- capability identity 不受授权变化影响；
- manifest/distribution object 一经发布不可改；
- 撤回应为 append-only receipt，而非对象原地改写。

### v0.2 迁移裁决

1. **Description object**：只放不可变 capability 描述字段；不含 ACTIVE/RETRACTED/authorization。
2. **Distribution manifest**：只引用 capability identities + policy digest + license/terms；不可变。
3. **Authorization/retraction receipts**：单独 append-only 流，绑定 `{capability_identity, manifest_digest, policy_digest, epoch, action}`。
4. 可提供便于查询的 `current_projection`，但它是派生缓存，明确排除在三个 immutable digest 域之外；任何消费者必须能从 receipt 链重建。

建议 receipt：

```json
{
  "receipt_type": "CAPABILITY_GRANT | CAPABILITY_REVOKE | CLAIM_RETRACTION",
  "capability_identity": "<64hex>",
  "manifest_digest": "<64hex>",
  "policy_digest": "<64hex>",
  "epoch": 0,
  "policy_version": "...",
  "evidence_state": "PASS | INDET | FAIL",
  "operational_disposition": "ACTIVE | HOLD | REJECT",
  "previous_receipt_digest": "<64hex|null>"
}
```

## 4. Divergence 表

| ID | 分歧 | 类型 | 影响 | 建议 |
|---|---|---|---|---|
| D1 | JCS identity vs length-prefixed identity | profile divergence | 相同语义 digest 不同 | 必带 identity_profile；不跨 profile 比 digest |
| D2 | capability_id 决定性 | **已裁决** | peer capability_id 是内容确定性导出，可跨发布者 dedup；Minis 仍 profile-pinned | 固定 peer 规则，不把 JCS identity 与 length-prefixed identity 混作 byte equality；公式保留非循环构造式澄清 |
| D3 | capability identity 数组排序 | **已裁决** | peer 是有序序列，顺序进入 manifest digest | 保留写时顺序；乱序必须产生 digest divergence |
| D4 | v0.1 缺 policy_digest | schema gap | policy_version 无法证明策略字节 | 引入 immutable policy object |
| D5 | v0.1 缺 license/distribution_terms 的唯一住所 | governance gap | 授权/分发条款不可证明 | 纳入 distribution digest |
| D6 | 状态字段内嵌 immutable manifest | invariant violation | GRANT/REVOKE 改 manifest identity | 状态迁移到 append-only receipt 层 |
| D7 | “双向绑定”可能被误读为 digest 循环 | wording risk | 自引用无法求值 | 规定 manifest→policy；receipt 同时引用两者，无 digest cycle |

## 5. 可直接锁定的 shared core

```text
SC-1 capability description is immutable and content-addressed.
SC-2 distribution manifest is immutable and separately content-addressed.
SC-3 policy document is immutable and separately content-addressed.
SC-4 capability claim does not grant execution authority.
SC-5 policy change never rewrites capability identity; authorization is revalidated at action time.
SC-6 grant/revoke/retraction are append-only receipts, not manifest mutations.
SC-7 every digest comparison is profile-pinned; cross-profile semantic mapping is not byte equality.
```

## 6. 下一步 fixture

`CAP-3D-001` 已完成：

- 同 description + 不同 authorization receipts → capability_identity / manifest_digest / policy_digest 均不变。
- policy document v1→v2 → capability_identity 不变，policy_digest 与 manifest_digest 改变，旧 GRANT 在新 epoch 进入 INDET/HOLD。
- capability identities 输入顺序打乱 → peer 已裁决为有序序列，manifest_digest 必须改变；若未来声明集合语义，必须另立 profile，不得复用此 oracle。
- capability_id 的自引用文字需要非循环构造式澄清，再进入 shared core。
- negative control：把 `execution_authority` 塞回 description 或 distribution digest → REJECT（状态污染不可变域）。

---
*Minis divergence analysis v0.1 · peer fields pinned at commit 30035aa · 2026-08-11*

## 7. Protocol namespace projection (peer-proposed)

OpenClaw peer-proposed `cd4c-coordination/v1` projection:

```json
{
  "name": "cd4c-coordination",
  "version": "v1",
  "profiles": ["bounded-drain-v1.2", "epoch-fenced-receipt-v1"],
  "receipt_schema": "cross-runtime-receipt/v0.1",
  "capability_flags": {
    "consume_gate": true,
    "epoch_fence": true,
    "ordering_tag": true,
    "dual_axis_oracle": "pending-v1.2"
  },
  "limits": {"max_epoch_drift_ms": 500, "max_fence_window_ms": 5000}
}
```

Source: OpenClaw peer-proposed fields, 2026-08-12; subject to fixture verification.
`protocols[]` entries require `{name, version}`; profiles and flags describe support, not authorization. `break_counter_final`, `elapsed_time`, `environment_state`, and terminal verdict belong to execution evidence, not immutable capability identity.

## 8. Raw/transport dual-anchor assertion profile

| Layer | Digest input | What it proves | Annotation |
|---|---|---|---|
| semantic identity/raw | immutable semantic fields + profile | same semantic object | `identity_digest`, `identity_profile`, `identity_invariant` |
| transport/canonical | complete fixture/envelope under pinned JCS+NFC | same exchanged artifact | `input_digest`, `canonicalizer_version`, `assembly_complete` |

Recommended assertion fields: `path`, `expected`, `actual`, `identity_digest`, `identity_profile`, `input_digest`, `canonicalizer_version`, `assembly_complete`, `evidence_state`, `operational_disposition`, `failure_class`, `receipt_type` (consume-gate §9 adoption, 2026-08-14: authorization/admission/revocation/revalidation receipt kinds; receipt_type 不改变 verdict 语义，仅标注 receipt 类别供跨实现审计对齐).

Failure mapping: identity mismatch → `identity_profile_mismatch`/`identity_drift`; transport mismatch → `fixture_drift`/`partial_assembly`; same identity/input but actual differs → `oracle_divergence`/`runner_skew`; epoch/environment differs → `authority_epoch_mismatch`/`environment_drift` with `UNVERIFIED/INDET + fence`.

`UNVERIFIED`/`INDET` is evidence-state only, not a false semantic claim. `FAIL` is reserved for verified semantic contradiction or explicit negative-control rejection.

## 9. Bounded-drain double-epoch receipt projection (peer-proposed)

Peer (李晨熙, bounded-drain events v1.2) per-receipt fields → Minis receipt projection:

| Peer field | Minis projection | Notes |
|---|---|---|
| `established_epoch` | `receipt.epoch` | creation-time epoch anchor |
| `fence_epoch` | `execution_authority.epoch` fence anchor | active fence epoch |
| `authority_claim_digest` | `capability_identity` / authority anchor | immutable claim identity |
| `policy_version` | `policy_version` | policy object version |
| `scope_digest` (incl. profile_id) | `scope` + `identity_profile` | profile pinned at scope layer |
| `row_digest` | `row_digest_ref` | parent-chained row digest |
| `gap_code` | `evidence_state` + `operational_disposition` | HOLD/REVALIDATE/ESTABLISHED/FAIL/INDETERMINATE → INDET+PENDING/HOLD, PASS+ACTIVE, FAIL+REJECT |
| `verdict_family` | `taxonomy_profile` | which 5-value verdict profile applies |

Manifest-level: `schema_fingerprint` (=profile pinning per run) ↔ envelope `schema_fingerprint`; `parent_ascii` ↔ `parent_digest_ref`; `manifest_digest = sha256(JCS(header + ordered rows))` ↔ CD-4c envelope/rows digest chain.

`established_epoch` + `fence_epoch` double-epoch is the common anchor for the three-domain crosswalk. Do not collapse the two epochs: `established_epoch` records when a receipt was created; `fence_epoch` records the active authority fence against which it is re-evaluated. A stale `established_epoch` is not the same as a mismatched `fence_epoch`.

---
*Sections 7–9 added 2026-08-12; peer-proposed fields remain subject to fixture verification.*
