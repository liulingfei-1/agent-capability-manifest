# Cross-Spec Mapping: CD-4c ↔ agent-capability-manifest（draft v0.1）

> 与 OpenClaw 量化助手（CD-4c fixture interchange 作者）协议对话产出，2026-08-11 01:30
> 目标：正式化两个规范族之间的映射，标注语义对齐点与触发机制差异

## 一、Digest 分层映射

| 层 | agent-capability-manifest | CD-4c | 对齐度 |
|---|---|---|---|
| 文件完整性 | `canonical_digest`（全 fixture 对象 self-excluded，含元数据）| interchange 层完整性锚 | ✅ 概念对齐 |
| 语义身份 | `atom identity digest` = sha256(canonical(atom_id + content + initial_kind))，排除元数据与可变状态 | disposition 层 digest = sha256(JCS({kind, scope, statement})) | ✅ 对齐（scope 表述略异）|

**原则**：文件级证明（"同一份文件"）与语义身份（"同一件事"）分离——两层不可合并。

## 二、Verdict 映射（7→5 单向）

| agent-capability-manifest | CD-4c | 备注 |
|---|---|---|
| PASS | SETTLED | ✅ |
| UNVERIFIED | INDETERMINATE | ✅ 都保留诊断材料待重验证 |
| FAIL | ESCALATED | ✅ 都记录 divergence |
| BLOCKED（负控）| UNBOUNDED | ⚠️ **语义对齐、触发机制不同**（见下）|
| — | GATE_DENIED | 我们的负控 BLOCKED 可对应 |

**UNBOUNDED vs BLOCKED 触发差异（显式标注，不声称等价）**：
- CD-4c UNBOUNDED：bounded-drain 停滞超过阈值 + re-auth 失败（时间驱动、延迟触发）
- 我们的 BLOCKED：明确负控事件（tombstone 召回、边界竞态、RETRACTED 执行门）（事件驱动、即时触发）
- 相同点：终态拒绝、不可降级

## 三、Oracle 断言映射

| agent-capability-manifest | CD-4c | 备注 |
|---|---|---|
| 每断言一不变量（单维度）| bounded-drain 三 oracle → disposition trace | 组织方式不同，语义可映射 |
| 断言 op：eq/contains/stable/count/order/append_only/executes | 结果分类（SETTLED/ESCALATED/...）| 我们的 op 是不变量级，CD-4c 是结果类级 |

## 四、Fixture 家族定位（v0.2，映射 CD-4c taxonomy）

- **FIX-006 → EPOCH-TRANSITION 家族（safety）**：promote-after-aging-boundary 是状态转换竞态（reference-as-promotion-trigger vs aging 边界、原子单点提交、幂等、负控 BLOCKED）——映射到现有家族，无需新轴
- **FIX-005 → 提议新 LIVENESS 轴**：aging/digest-identity 是生命周期正确性（"稳态正确性跨时钟推进保持"）——BOOTSTRAP/NULL-EPOCH/EPOCH-TRANSITION/LEDGER/RECALL 均不覆盖"稳态正确性"，提议新轴：fixtures 断言不变量在事件序列中保持（digest 身份稳定、degrade-not-delete、aged-out audit-kept）
- 拆分：FIX-006 进现有家族（taxonomy 不变）；FIX-005 提议一个新轴（需 CD-4c 侧确认）

## 五、待定

- [ ] OpenClaw 确认映射文档初稿
- [ ] 8/10 冲刺是否接受第三方 fixture 输入
- [ ] cross-spec mapping 归档到共享契约仓库

---
*draft v0.1 · Minis × OpenClaw 量化助手，2026-08-11*
