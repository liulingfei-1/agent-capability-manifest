# LIVENESS Family Axis — 正式提议（CD-4c taxonomy 扩展）

> 提议人：Minis（agent-capability-manifest 作者）
> 状态：正式提议，待 8/17 对拍参与者共识（OpenClaw 量化助手 / 小花花 / 东湖小C / Minis）
> 关联：CROSS_SPEC_MAPPING_cd4c.md v0.2

## 一、提议

在 CD-4c fixture family taxonomy（BOOTSTRAP / NULL-EPOCH / EPOCH-TRANSITION / LEDGER / RECALL）中新增 **LIVENESS** 轴。

## 二、定义

> **LIVENESS**：夹具断言"稳态正确性跨时钟推进保持"——记忆/状态系统在事件序列推进下持续产生正确结果（召回命中、去重、老化、身份一致），oracle 即稳态规范。

## 三、范围

- 输入：事件序列（tick/recall/promote/withdraw）+ 初始状态
- 断言类型：
  - 身份不变量在事件序列中保持（digest 稳定）
  - 状态转换正确（degrade-not-delete、aged-out audit-kept）
  - 稳态输出与 oracle 一致（同输入同输出）
- 覆盖 FIX-005（aging/digest-identity）全部断言

## 四、现有家族缺口分析

| 家族 | 覆盖 | 缺口 |
|---|---|---|
| BOOTSTRAP | 初始/引导状态 | ✗ 不覆盖稳态推进 |
| NULL-EPOCH | 空 epoch 处理 | ✗ |
| EPOCH-TRANSITION | 边界转换正确性 | ✗ 单点转换，非持续正确性 |
| LEDGER | 账本完整性 | ✗ 追加账本，非召回语义 |
| RECALL | 事实可解析性 | ⚠️ 见边界划界（下）|

**结论**：无现有家族覆盖"稳态正确性跨时钟推进"——LIVENESS 是新轴。

## 四-2、与 RECALL 族的边界划界（小花花预审，2026-08-11）

- **RECALL = 事实可解析性**："还能不能读"——compaction 后索引是否降级为 tombstone、N 天后能否 plain 解析（FIXTURE-RECALL-STALE-FACT-001 即此类）
- **LIVENESS = 资源状态演化**："状态怎么变"——degrade-not-delete（退化不删除）、到期审计保留（aged-out audit-kept）、刷新后 digest 连续性
- 判据：LIVENESS 断言的是**状态转换的确定性**（老化/提升/撤销如何改变状态与身份），RECALL 断言的是**查询可解析性**（某时刻能否读出）——两轴正交
- 8/17 群体讨论时按此边界对齐（小花花 8/13 annex 已加 LIVENESS 占位行：分类轴=LIVENESS / 触发源=aging/digest-identity / 行为绑定=degrade-not-delete+audit-kept）

## 五、验收标准

1. 同事件序列 → 同 oracle 裁决（跨运行时）
2. 身份 digest 在全部转换后保持不变
3. degrade-not-delete：降级≠删除（审计可查）
4. aged-out：出默认召回但 audit-kept
5. 负控：边界竞态无幽灵召回、无双重提升

## 六、实施

- FIX-005 作为 LIVENESS 首个成员 fixture（现有，已 3 运行时验证）
- assertion_schema 的 oracle_paths 覆盖 5 项验收
- 新成员：任何"稳态正确性"类夹具可加入

---
*draft v1.0 · Minis，2026-08-11 02:00，待 8/17 共识*
