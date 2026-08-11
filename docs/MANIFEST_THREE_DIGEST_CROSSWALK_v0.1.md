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
| capability_id | 进入 digest | atom_id 通常由内容构造/映射 | 待冻结：若 capability_id 是任意发行方 ID，同语义不同 ID 会产生不同 identity |
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
| capabilities | identity 列表 | tools/skills 对象数组 | 应先投影为 identity 列表再算分发 digest |
| license/terms | 唯一合法住所并入 digest | v0.1 schema 缺失 | 真缺口，应新增 |
| 数组顺序 | JCS 对数组顺序敏感 | 未冻结 | **待决**：若 capability 集合无序，hash 前必须按 64hex identity 排序；否则排序差异造成伪 drift |

**共享核心建议**：

```json
{
  "manifest_id": "...",
  "version": "0.2",
  "policy_digest": "<64hex>",
  "capability_identities": ["<64hex sorted ascending>"],
  "licenses": [...],
  "distribution_terms": [...]
}
```

- 若 `capability_identities` 语义是集合，规范必须要求按 lowercase 64hex 升序后再做 JCS。
- 若顺序承载优先级，则必须声明 `ordering_semantics`，不得静默排序。

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
| D2 | capability_id 是否为内容决定值 | identity ambiguity | 任意 ID 破坏跨发布方去重 | 定义 deterministic capability_id 或从 identity 输入移除 |
| D3 | capability identity 数组排序未冻结 | canonicalization ambiguity | 同集合不同顺序 → manifest drift | 明确集合排序或 ordering_semantics |
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

建议新增 `CAP-3D-001`：

- 同 description + 不同 authorization receipts → capability_identity / manifest_digest / policy_digest 均不变。
- policy document v1→v2 → capability_identity 不变，policy_digest 与 manifest_digest 改变，旧 GRANT 在新 epoch 进入 INDET/HOLD。
- capability identities 输入顺序打乱 → 若声明集合语义，manifest_digest 必须不变；若声明顺序语义，必须显式不同。
- negative control：把 `execution_authority` 塞回 description 或 distribution digest → REJECT（状态污染不可变域）。

---
*Minis divergence analysis v0.1 · peer fields pinned at commit 30035aa · 2026-08-11*