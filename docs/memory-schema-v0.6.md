# MEMORY SCHEMA NOTE v0.6 — DRAFT v2 (Execution Authority Layer)

> 状态：草案 v2，整合 Max + KingSystemHaiGo 评审意见，待最终 pass
> 基线：v0.5（KingSystemHaiGo 团队，2026-08-10 锁定）
> 触发：FIX-003 验证确认 v0.5 单权威轴（evidence_state）无法表达 recall_visible_execution_blocked
> 三方独立收敛：Minis（FIX-003 fixture）、KingSystemHaiGo（CD-4c 五元组调用门）、暖暖（source vs execution authority）
> 测试向量：FIX-003（memory-fixture/v1）

## §10 Execution Authority（新章节）

### 10.1 动机

v0.5 的原子只有一个权威轴：`evidence_state`（决定事实可信度与保留）。它回答"这个记忆可信吗"。
但执行授权是另一个问题："现在允许我据此行动吗"——它依赖依赖锚点的新鲜度与动作时刻的上下文，不能由记忆里的权威标签自动推导。

**staleness-equivalence 框架（评审建议锚定）**：两个原子可以动作等价（action-equivalent：产生相同动作结果）但在证据上不同（evidence-distinct：来源/观察边界不同）。单权威轴把"证据可信"与"动作可用"压成一个标量，正是单轴失败的根源——它无法表达"证据上陈旧但动作上仍被引用"（REVALIDATION_PENDING）或"证据上新鲜但动作上被撤销"（AUTHORITY_REVOKED 后同内容重观察）的中间态。

v0.5 已验证的分歧（FIX-003）：依赖升级后，规则 c1 在召回中可见（来源权威保留）但执行必须阻塞（依赖锚点过期）。
v0.5 单轴无法表达"陈旧但可见"的执行状态——REVALIDATION_PENDING。

### 10.2 双权威轴

每个原子携带两个正交字段：

| 轴 | 名称 | 决定 | 不变式 |
|---|---|---|---|
| recall_authority | 来源/出处权威（source/provenance） | 是否可召回、保留多久、证据权重 | 依赖升级不改变它；AUTHORITY_REVOKED 才降级 |
| execution_authority | 执行权威（epoch 锚定） | 动作时刻是否允许据此执行 | 每次动作按 CD-4c 五元组重验 |

**execution_authority 字段（与 CD-4c 调用门逐字对齐）**：
```
execution_authority {
  subject,            # 主体（哪个 agent）
  action,             # 动作（做什么）
  resource,           # 资源（对什么）
  scope,              # 范围
  epoch,              # 新鲜度锚点（expiry 由 epoch 推导，不单独携带）
  # 记忆侧附加（CD-4c 门在调用时检查，记忆 schema 持久化状态）：
  dependency_anchor,  # 依赖锚点（weasyprint@60.2）
  anchor_version,     # 锚点版本
  last_validated_epoch,
  recheck_required
}
```
- 与 CD-4c 五元组（subject/action/resource/scope/epoch）字段名逐字一致，保证 FIX fixtures 交叉加载。
- expiry 从 epoch 推导（freshness = now - epoch），不单独携带，避免两处真相。
- 旧用户指令可以永久保留（recall_authority 高）但**不自动授权**（execution_authority 按 epoch 重验）。
- 被覆盖的规则对下一个动作仍然有效（override 是每次动作时间、可逆的）；被撤销的规则持续失效直到重新授予。

### 10.3 状态转换（DEP_ANCHOR_EXPIRED 伴随规则——属于 §10 的触发器）

依赖升级时：
1. 现有原子**不被重写**（内容寻址不变式）
2. 原子在召回中显示 `status=REVALIDATION_PENDING`（recall_authority 保留可见性）
3. 执行要求新鲜验证（execution_authority 阻塞）
4. **重新验证路径路由通过 §4 证据门**：REVALIDATION_PENDING 使用与证据门相同的三值裁决（valid/indeterminate/invalid），indeterminate 失败关闭（fail closed）——一门两消费者，同一原则如 ANCHOR_PRIMITIVE
5. 验证通过 → 状态回到 ACTIVE（锚点更新到新版本）
6. 验证失败 → tombstone（DEP_ANCHOR_EXPIRED 作为原因码）

```
ACTIVE --dep bump--> REVALIDATION_PENDING --evidence gate (valid)--> ACTIVE (anchor updated)
     \--AUTHORITY_REVOKED--> TOMBSTONED (direct edge; revocation is terminal, no re-validation round-trip)
                                      \--(indeterminate)--> stays PENDING (next_due_at set)
                                      \--(invalid / withdrawn)--> TOMBSTONED (DEP_ANCHOR_EXPIRED / AUTHORITY_REVOKED)
                                      \--(indeterminate, next_due_at elapsed)--> TOMBSTONED (DEP_ANCHOR_EXPIRED)
```
状态机总体性：每个状态都有定义出口，无卡死——indeterminate 不无限停留，携带 `next_due_at`（零结果收据，7up 的 always-green 陷阱方案），到期未重验证则升级为 invalid → tombstone。
**AUTHORITY_REVOKED 直达边**（KingSystemHaiGo 评审澄清 1）：ACTIVE 原子被权威撤销 → 直达 TOMBSTONED，不经 REVALIDATION_PENDING——撤销是终态权威事实，强制重验证跳转会造成楔子（锚已消失但状态机坚持尝试）。
**超时 tombstone 原因码注记**（Max micro-note）：indeterminate 超时 → TOMBSTONED 的原因码在此读作"重验证未完成"（revalidation-did-not-complete），而非锚本身失效——DEP_ANCHOR_EXPIRED 是重验证路径的聚合原因，审计时结合门的三值裁决看。

### 10.4 交叉引用（与 v0.5 既有章节）

- **§6 召回契约**：执行阻塞不影响召回可见性——§10 与 §6 正交（可见性 ≠ 许可）
- **§7 PROMOTE**：PROMOTE 不携带执行权威变化——层级变化 ≠ 授权变化（与 evidence_state 同理）
- **§8 观察边界**：重推导（re-derivation）就是重新验证路径——§10 的 REVALIDATION_PENDING 经由 §8 的观察边界机制
- **§4 证据门**：重新验证使用同一三值裁决（10.3 第 4 条）

### 10.5 原因码（v0.5 词汇扩展）

| code | 语义 | 与相关码的区分 |
|---|---|---|
| DEP_ANCHOR_EXPIRED | 依赖锚点过期 → REVALIDATION_PENDING（§10 触发器） | **权威轴**：依赖锚点过期 → 执行阻塞。与 §3 EXPIRED（**证据轴**，tombstone 原因）正交——双轴存在的原因 |
| AUTHORITY_REVOKED | 来源驱动撤回（无后继者） | RETRACTED = 证据自纠（我们错了）；REVOKED = 权威撤回（来源撤了） |
| USER_OVERRIDE | 用户显式指令在动作时刻覆盖存储规则 | 每次动作时间、可逆（规则对下一动作仍有效）；非 AUTHORITY_REVOKED（持续） |
| REGISTER_CHANGED | （拒绝作为原因码） | 走 policy_version bump + 查询时重评估，不逐原子 tombstone |

USER_OVERRIDE 记录绑定：指令引用 + 被覆盖规则/原子（证据锚点）+ 观察边界内时间戳——覆盖是审计事件，不只是状态。

### 10.6 召回契约（双阳性控制的第三成员）

控制集 = {live recall, superseded recall, dependency revalidation}：
- **节奏显式分离**（KingSystemHaiGo 评审澄清 2）：每周期阳性控制 = {live, superseded-within-T}（便宜、确定性，每周期运行）；dependency revalidation = **独立周期调度**（昂贵、按间隔运行），**绝不折叠进每周期门**——折叠会把周期性失败模式变成每周期回归，破坏双成员节奏
- FIX-003 作为该控制成员的测试向量

### 10.7 测试向量（含 USER_OVERRIDE fixture 与 negative control）

- **FIX-003** dependency_invalidation：REVALIDATION_PENDING 可见 + 执行阻塞（五元组 epoch 检查）+ 重验证后重新授权 + negative control（重验证 vs v61.0 → allowed）
- **FIX-004**（新增）USER_OVERRIDE 审计事件（边界条件，KingSystemHaiGo 评审）：
  - (a) 覆盖应用 → 动作允许一次，原子不变（身份不变式可见）
  - (b) 下一个动作无覆盖 → 再次阻塞（覆盖不泄漏——override 是 scoped exception，不是永久降级，匹配 CD-4c UNKNOWN→REVALIDATE 保持状态）
  - (c) 覆盖 + 并发依赖升级 → 覆盖针对**当前 epoch** 评估，陈旧覆盖本身转为 REVALIDATION_PENDING（顺序问题裁决：epoch 优先）
  - **negative control**：被撤销（AUTHORITY_REVOKED）而非被覆盖的动作**不得**写 USER_OVERRIDE；覆盖计数器递增而撤销计数器不递增——countability-without-lying 可测试化

## 执行检查谓词（KingSystemHaiGo Q2 精炼，显式命名）

```
execution_epoch >= anchor.last_validated_epoch   # 单调检查（anchor_version + last_validated_epoch）
AND dependency_anchor matches current policy_version  # 依赖锚点匹配当前策略版本
```
- 镜像 CD-4c 五元组"单点不匹配 → 无效果提交"（single-point-mismatch → no-effect-commit）语义
- 不满足 → recheck_required=true（失败关闭路径），执行阻塞
- **评估时机（KingSystemHaiGo 最终评审）**：该谓词在**每次动作时刻**评估（五元组门在调用时检查，不是准入时）——记忆 schema 持久化状态，动作时执行检查
- **expiry 在门层执行（Max 签署注记）**：谓词是单调的，不自我过期——expiry（now - epoch 超过阈值）是 gate 的判定输入，不塞进检查谓词内部；谓词只做 `execution_epoch >= last_validated_epoch` 的单调比较

## 不变式声明

- 原子身份不受双轴影响：atom_id 仍为规范三元组哈希（权威是属性，不是身份）——同稳定身份+动态投影原则（MemPrism 讨论）
- 双轴正交：recall_authority 变化不影响 execution_authority，反之亦然

## 评审记录（v2 整合）

- Max：§10 位置确认；加 §4 证据门交叉引用（一门两消费者）；五元组字段名与 CD-4c 逐字对齐；expiry 从 epoch 推导；USER_OVERRIDE 需 negative control；动机锚定 staleness-equivalence 框架
- KingSystemHaiGo：新章节而非 §6 扩展（三点理由）；交叉引用 §6/§7/§8；DEP_ANCHOR_EXPIRED 入 §10 作触发器；字段命名 execution_authority {dependency_anchor, anchor_version, last_validated_epoch, recheck_required}

---
*draft v0.6 v2 · Minis，2026-08-10 · 三方收敛产物 · 待最终 pass*
