# Digest 碰撞/歧义测试向量（v0.2 材料，小吉量评审项）

> 用途：验证内容寻址 digest 的确定性（same capability → same hash）与区分性（different capability → different hash）
> canonicalizer：严格 JCS RFC 8785（canonicalizer_version=1.0，对齐 CD-4c 6c3158e）+ NFC mandatory + UTF-8/LF + 无终止换行 + self-excluded

## 一、同 canonical → 同 digest（确定性）

| # | 变体 | 期望 |
|---|---|---|
| D1 | 同一 JSON 对象，不同键输入顺序 | 同 digest（JCS 排序归一化）|
| D2 | 同一对象，不同空白（缩进/换行）| 同 digest（compact 归一化）|
| D3 | 同一对象，Unicode NFC vs NFD 形式 | 同 digest（NFC mandatory）|
| D4 | 同一对象，CRLF vs LF | 同 digest（LF 归一化）|
| D5 | 同一对象，键序不同 + 嵌套 | 同 digest（递归排序）|

## 二、不同 canonical → 不同 digest（区分性）

| # | 变体 | 期望 |
|---|---|---|
| C1 | 内容改一个字 | digest 必须不同 |
| C2 | 键改名（同值）| digest 必须不同 |
| C3 | 值类型变（string ↔ number）| digest 必须不同 |
| C4 | 字段删除 | digest 必须不同（且 schema 校验 reject）|
| C5 | 数组顺序交换 | digest 必须不同（数组有序）|

## 三、fail-closed 负例

| # | 场景 | 期望行为 |
|---|---|---|
| N1 | 组装不完整（缺 events/oracle 节）| reject（79b86b21 教训：不得"缺了就少算一节"）|
| N2 | 重复键（JSON 解析歧义）| reject（parse-time typed failure）|
| N3 | 非 NFC 输入 | reject（NFC mandatory）|
| N4 | 撤回条目旧 digest 作 live 使用 | 拒绝（tombstone 锁）|
| N5 | 尾随换行（\n 结束）| digest 变化 → 对账失败（无终止换行规范）|

## 四、跨运行时（小吉量重点）

- 三运行时（iSH/CD-4c/Windows）跑 D1-D5 全同 digest = 确定性跨环境成立
- 实测：FIX-005 input digest 三方一致（e95e2cdb00b7 → v0.3 d73e84c3ceb67851 → v0.4 8cd161245579bd42）
- 未遇哈希碰撞（64 位 sha256）；遇到的是工具链偏差（组装 bug / canonicalizer profile）——测试向量正是要消灭这类偏差

## 五、实现

runner 侧在 digest 计算前做 JCS 序列化 + NFC 归一化；测试向量作为 v0.2 regression 套件的一部分（T-digest-001 族）。

---
*draft v0.1 · Minis，2026-08-11 04:00，v0.2 评审材料*
