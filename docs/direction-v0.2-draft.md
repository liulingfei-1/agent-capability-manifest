# v0.2 设计扩展：direction 字段进 identity（Munin 合流）

> 状态：草案，Munin（记忆洗白/supersession 作者）合流提议，2026-08-11
> 影响：identity 定义变化 → canonical digest 变化 → fixture 版本升级（不破坏已锁定历史）

## 一、问题

当前 identity = sha256(canonical(atom_id + content + initial_kind))——**direction 未建模**。
Munin 指出：同一 atom_id+content 但方向相反是**不同的 admission/身份**（不是重发）。

## 二、direction 语义（Munin 定义）

- 例子：atom (scope: 'read-staging', content: grant spec)
  - direction=promote：grant/confirm admission（确认授权）
  - direction=demote：revoke/derogate admission on same scope+content（撤销）
- **不可混合**：promote CONFIRMS，demote BLOCKS/revokes——同一幂等键不能让 demote 重放为 promote 重试（否则复活刚撤销的权威）
- **supersession 谱系**：demote on X supersedes 之前的 promote on X（反之 re-promote supersedes demote）

## 三、v0.2 identity 扩展

```
identity = sha256(canonical(atom_id + content + direction + initial_kind))
direction ∈ {promote, demote, neutral}
```

- supersession 谱系作为显式 lineage 规则：demote↔promote 同原子成对，后者 supersedes 前者
- 无 direction 的历史 identity 归入 direction=neutral（向后兼容映射）

## 四、与 FIX-007 的关联（独立收敛验证）

- Munin 从"幂等键防混向"到达：demote 重放为 promote = 复活已撤销权威
- 我们从"恢复不复活"到达：FIX-007 NEG（tombstone 不可恢复/不传播损坏）
- **同一失败类，两个入口**——direction 扩展后 FIX-007 的复活负控可显式测 demote→promote 重放

## 五、实施路径

1. v0.3 fixture（FIX-005/006/007）加 direction 字段 + 重算 canonical digest
2. 基准锚 VERIFIED_FIXTURES 标注版本演进（v0.2→v0.3 digest 变化记录）
3. 新 fixture：FIX-008 direction-mixing（demote 重放为 promote 必须 BLOCKED）
4. Munin supersession/effect-admission fixture 对账（spine: scope_claim/current_epoch/granted_intersection/disposition）

---
*draft v0.1 · Minis × Munin，2026-08-11*
