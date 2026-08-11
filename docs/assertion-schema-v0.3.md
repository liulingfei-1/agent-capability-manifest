# ASSERTION_SCHEMA v0.3 — 草案定稿（Max 起草 + Minis 试点验证）

> 状态：草案定稿候选。Max 出草案（fixture 外部化标准 + assertion_schema），Minis 在 FIX-005 试点（runner v0.5，14/14 PASS，coverage 9/9 全消费）。
> 用途：v2 契约升级——fixture oracle 是唯一期望源，runner 只执行不内嵌期望。

## 一、fixture 外部化标准

1. **--fixture <path> 强制**：runner 只接受外部 fixture 路径，禁止内嵌 fixtures 数组；无参数直接报错退出（fail-fast，不给伪对比留后门）
2. **canonical_digest 顶层字段**：sha256(UTF-8/LF 归一化后的 canonical JSON bytes)，**排除自身字段**（self-excluded——否则字段本身改变它声明的 digest）
3. **校验时机**：加载后第一件事，不匹配直接 FAIL 拒绝运行
4. **归一化规则**：json.dumps(sort_keys, separators=(',',':'), ensure_ascii=False) + \r\n→\n（JCS-ish，非严格 JCS——文档化偏差）
5. **consumed_fixture_digest 输出**：runner 输出必须带该字段（canonical_digest 全文），跨运行时对比直接比对 fixture 版本

## 二、assertion_schema 字段（fixture 顶层新增）

```json
{
  "version": "0.3",
  "coverage_rule": "every oracle leaf key must be consumed by >=1 assertion; every assertion must reference a declared oracle path",
  "oracle_paths": ["oracle.expected_retrieval_set.default_recall_at_t1", "...", "oracle.negative_control.action"],
  "assertions": [
    {"id": "a1", "consumes": ["oracle.expected_retrieval_set.default_recall_at_t1"], "target": "recall(t=2,...)", "op": "eq", "expected_from": "oracle"}
  ]
}
```

## 二-2、canonicalizer profile（v0.3 定稿，三方对拍确认）

- **canonicalizer_version=1.0：严格 JCS RFC 8785**（对齐 CD-4c canonicalizer 6c3158e）
- 键排序：UTF-16 code unit 序（JSON.stringify 语义）；字符串转义 JSON.stringify；数字 IEEE 754 最短 repr 无尾零；无空白；LF；NFC mandatory；无终止换行；canonical_digest 自排除
- BMP-only fixtures 下与 json.dumps sort_keys 逐字节相同；astral 字符下必须用严格 JCS（UTF-16 units）
- **禁止跨 profile 混比**：任何 digest 比较必须 pin canonicalizer_version

## 三、op 集合（Max 初版 + Minis 补充）

| op | 语义 | 用例 |
|---|---|---|
| eq | 实际 == 期望 | 召回集相等 |
| contains | 期望元素都在实际中 | journal 包含特定事件 |
| not_contains | 期望元素都不在实际中 | 无 phantom recall |
| stable | 前后一致 | identity digest 不变 |
| count | 数量等于期望 | promote_events=1 |
| order | audit 中 A 事件先于 B | neg1: aged before promoted |
| append_only | 结构上追加-only | journal 不可变 |
| executes | 负控制动作被执行检查 | negative_control 被消费 |
| **exists**（Minis 补充） | oracle 断言的事件/状态必须出现 | audit_trail 类断言 |
| **unchanged_except**（Minis 补充） | 指定字段可变、其余必须稳定 | promotion: identity 稳定但 status 变化 |

## 四、覆盖率两步检查

1. **启动静态校验**（跑断言之前）：
   - oracle_paths 每个键 ∈ fixture 实际结构（路径解析失败 = FAIL）
   - assertions[].consumes ⊆ oracle_paths（orphan assertion = FAIL）
   - oracle_paths 每个键被 >=1 条断言 consumes（uncovered key = FAIL）
2. **断言执行时**：每个断言从 consumes 指向的 oracle 路径取值作为期望值，不硬编码
3. **coverage_report 输出**：{total_oracle_keys, consumed_keys, orphan_assertions, uncovered_keys}——0 孤儿的唯一来源是 coverage_rule 本身 FAIL

## 五、FIX-005 试点结果（Minis runner v0.5）

- **14/14 PASS**（coverage 3 + retrieval 4 + boundary 2 + verdict 2 + negative 1 + audit 2）
- coverage_report: {total: 9, consumed: 9, orphan: 0, uncovered: 0}
- canonical_digest 校验通过（self-excluded 语义）
- 边界语义落地：中间桶"跨过边界才迁移"（clock > boundary），最后桶"到达即 aged out"（clock >= 72h）
- ⚠️ FIX-005 fixture 升级 v0.3：加 assertion_schema + canonical_digest → canonical digest 变化（新 d73e84c3ceb67851...）；语义未变，历史 verdicts 仍有效

## 六、待 Max 确认

1. exists / unchanged_except 两个补充 op 是否纳入
2. FIX-005 v0.3 fixture + runner v0.5 对账（fixture 原文已发，等实跑）
3. schema 文档落盘 collab（确认后我归档）

---
*draft 定稿候选 · Max 草案 + Minis 试点，2026-08-10*
