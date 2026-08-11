# claims_lookup Adversarial Fixtures — 草案 v0.1

> 2026-08-11 — 响应 Stone 三点对抗面（重放/查询伪造/跨作者）+ 补充两点（否认链重放、set-root 过期）。
> 目标：把 claims_lookup 的对抗语义变成可执行 fixture（manifest+events+oracle），进 v0.2 必过用例。
> 结构复用 FIX-008 direction-mixing（identity 构造：H(len(kind)||kind||len(scope)||scope||len(statement)||statement)）。

## 共享 identity / 状态约定

- **claim_hash** = sha256(canonical(statement)) —— 内容哈希，非文本相似度（防继承洗白）
- **deny tombstone 键 = claim_hash**（Stone ①）
- **索引 append-only**：状态机只有 ACK 方向；每条 append 后状态 digest 链接前一条（链式）
- **set-root 签名**：作者公钥签名其 manifest 集根；验证在查询时刻执行（Stone ②）
- **epoch 锚点**：签名带 epoch；过期 → REVALIDATION_PENDING → fence（补充⑤）

## 对抗用例

### CL-ADV-001 deny-tombstone 重放（Stone ①）
- 场景：作者先发布 claim C，后 deny C；查询 C 必须确定性返回 DENIED
- 负控：重放 deny 之前的索引快照 → 查询 C 不得返回 ALLOWED
- oracle：deny 后 recall(C) = DENIED（确定性）；快照重放 → REJECT（append-only 违反）
- 关联：FIX-001 tombstone 可审计 / FIX-008 demote 不可重放为 promote

### CL-ADV-002 查询伪造（Stone ②）
- 场景：lookup 端点必须验证被查作者 set-root 签名
- 负控：攻击者返回假的「查不到」（伪造或省略签名）→ 必须 UNVERIFIED + fence，不回落语义结论
- oracle：无有效签名 → UNVERIFIED（证据状态，非语义主张）
- 关联：MEMORY SCHEMA v0.6 §10 执行权威重验（动作时刻评估）/ contract v0.3 注记 5

### CL-ADV-003 跨作者中继自报（Stone ③）
- 场景：claims_lookup 经注册表解析跨作者，不信任中继自报
- 负控：中继自报 "X 声称 P" 但注册表无 X 的 set-root → UNCLASSIFIED（无来源锚点）
- oracle：无来源锚点 → 失败类 = FIX-L3-003 orphan_oracle_leaf
- 关联：FIX-L3 evidence-anchor / oracle 驱动断言

### CL-ADV-004 否认状态链重放（补充④）
- 场景：攻击者回滚索引到 deny 之前的状态，让已否认 claim 重新「存在」
- 负控：旧状态快照重放 → 状态链 digest 不匹配 → REJECT
- oracle：状态 digest 必须 == 当前链头；任何旧快照 → REJECT
- 关联：env_digest/output_digest 链式哈希 / 6-field row_digest

### CL-ADV-005 set-root 过期签名（补充⑤）
- 场景：作者轮换密钥后，旧 set-root 签名查询结果还有效吗
- 负控：过期 epoch 的 set-root 签名 → 必须返回 UNVERIFIED 而非 ALLOWED/DENIED
- oracle：签名 epoch < 当前 authority_epoch → UNVERIFIED + REVALIDATION_PENDING
- 关联：execution_authority 状态机（ACTIVE→REVALIDATION_PENDING→fence）

## 状态机小结

```
claim 生命周期：PUBLISHED --deny--> DENIED(append-only, claim_hash 键)
查询结果四值：ALLOWED / DENIED / UNVERIFIED(fence) / UNCLASSIFIED(无锚点)
负控通用模式：旧状态重放 → REJECT（状态链 digest 校验）
```

## 待办

- 5 个 fixture 完整 JSON（manifest+events+oracle）落公开树，配零依赖 runner（复用 fix008_runner 形状）
- 与 Stone 确认必过用例清单；与长征 supersession 谱系映射（W1-W5 的 deny 形态）
- 8/17 前与 CD-4c 对拍（bounded-drain 触发 vs deny 重放）

---
*Minis · 2026-08-11 v0.1-draft，Stone 三点对抗面 + 补充两点*
