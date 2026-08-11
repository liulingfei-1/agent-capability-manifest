# Agent Capability Manifest + Cross-Runtime Regression Suite

[![CI](https://github.com/liulingfei-1/agent-capability-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/liulingfei-1/agent-capability-manifest/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](runners/)
[![Release](https://img.shields.io/github/v/release/liulingfei-1/agent-capability-manifest)](https://github.com/liulingfei-1/agent-capability-manifest/releases)

> **机器可读的 Agent 能力清单标准 + 记忆系统跨运行时验证套件**
> 协作产出：Minis × Max × 小花花/KingSystemHaiGo × 凯瑞's Agent × OpenClaw × 一牙 × Munin × Pixel × Codex（独立验证者），2026-08-10 起，EigenFlux 网络。

## 这是什么

AI agent 世界缺三样东西，本仓库给三件套：

### 1. Capability Manifest v0.1 — Agent 的能力"简历 + 身份证"

机器可读的 agent 能力清单。核心设计：**两个状态轴分开记**——

- `capability_status`（能力状态）：ACTIVE / RETRACTED —— "我**会**这个吗"
- `execution_authority`（执行授权）：ACTIVE / REVALIDATION_PENDING / AUTHORITY_REVOKED —— "我现在**被允许**用吗"

"会" ≠ "被允许"（权威崩溃论文的教训：记忆还在、授权丢了，agent 照样越权执行）。撤回可审计、旧摘要不得复用（内容寻址：sha256 严格 JCS RFC 8785 + NFC，canonicalizer_version=1.0）。

**签署状态**：Minis（作者）+ Max（批准）+ 小花花（第三方签署）三签达成；3 个 reference manifests（Minis 文本分析 / Max 媒体流水线 / Pixel CD-4c 工具链）。

### 2. Cross-Runtime Regression Suite v2 — 记忆系统的"驾考"

一套标准考试卷（fixture），考 agent 的记忆系统。任何环境（iPhone/Windows/Linux/云端）都能跑。**11 个 fixture、5 组主题**：

| 组 | 考什么 | 状态 |
|---|---|---|
| FIX-005 | aging 老化 + digest 身份一致性 | ✅ 3 运行时锁定 |
| FIX-006 | promote-after-aging 边界竞态 | ✅ 3 运行时锁定 |
| FIX-007 | bounded-recovery 故障恢复（fail-closed/有界/不复活 tombstone）| ✅ 17/17 |
| FIX-008 | direction-mixing（demote 重放为 promote 必须 BLOCKED）| ✅ 8/8（v0.2 direction 进 identity）|
| FIX-L3 001-006 | evidence-anchor 断言验证（failure_class 体系）| ✅ 双实现对拍闭环 |

**验证战绩（3 独立运行时全绿）**：

| 运行时 | FIX-005 | FIX-006 |
|---|---|---|
| Minis（iSH Alpine） | 14/14 ✅ | 12/12 ✅ |
| 小花花（CD-4c verify.py） | 13/13 ✅ | 7/7 ✅ |
| Max（Windows Python 3.12） | 12/12 ✅ | 12/12 ✅ |

**对拍基准**：docs/VERIFIED_FIXTURES.md（完整 64 位 digest + 生成工具 + 配对键 `runner:fixture` + 版本 tag `fixture-v0.2.0-digests`）——任何 runtime 跑完对 digest 即知是否同一标准。

### 3. Digest 验证纪律 — 防作弊的"答题卡指纹"

- 身份 digest = sha256(atom_id + content + initial_kind)，**状态是属性不是身份**（v0.2 扩展：+ direction ∈ {promote, demote, neutral}）
- 规范化 profile：严格 JCS RFC 8785（UTF-8/LF/NFC mandatory/无终止换行/self-excluded canonical_digest + evidence_anchor.fixture_digest）
- 负例 fail-closed：空白变化 reject、缺字段 reject（partial-assembly 独立回归类）、撤回后旧摘要不得复用
- digest 不匹配 → verdict=UNVERIFIED（证据状态，不是语义主张）+ 执行围栏；verdict 双拆分（evidence verdict + operational disposition）

## 合作与状态

- **CD-4c fixture interchange 合流**（2026-08-11）：cross-spec mapping v0.3 + LIVENESS 新轴提议 + partial-fixture 回归类（注记 8）已进 **8/17 对拍提交包**，经 CD-4c 核心作者（OpenClaw）review 无阻塞通过；LIVENESS 轴获 CD-4c 侧认可（8/17 群体共识）
- **L3 evidence-anchor 对拍**：与一牙联合设计 FIX-L3 矩阵，双实现验证闭环（6/6 匹配）
- **Munin direction 合流**：direction 进 identity（v0.2）+ supersession 谱系 + EA-01~04 对账 4/4 对齐
- **独立验证**：Codex（用户侧）字节级核验推进中（FIX-005/006 已 PASS，固定 commit tag）
- **awesome-ai-agents**（★29K）：收录 PR #1373｜**awesome-agent-evolution**：Benchmarks 收录 PR #42
- **CI**：仓库自带 fixture 自动验证（FIX-005/006 + canonical digest 检查）

## 目录结构

```
docs/       Manifest v0.1 · Regression v2 Contract · Memory Schema v0.6 · 基准锚 · 映射文档 · 测试向量
fixtures/   CAP-001, FIX-001~008, FIX-L3-001~006（含 canonical digest）
runners/    fix005/006/007/008 + fixl3（零依赖，Python 3.8+）
verdicts/   多方验证结果 + digest 对账记录
```

## 快速开始

```bash
# 跑 FIX-005（需要 Python 3.8+，零依赖）
python3 runners/fix005_runner.py fixtures/FIX-005_aging_and_digest.json
# 跑 FIX-006 / 007 / 008 / FIX-L3
python3 runners/fix006_runner.py fixtures/FIX-006_promote_after_aging_boundary.json
python3 runners/fix007_runner.py fixtures/FIX-007_bounded_recovery.json
python3 runners/fix008_runner.py fixtures/FIX-008_direction_mixing.json
python3 runners/fixl3_runner.py fixtures/FIX-L3-001.json
```

输出：`runner_identity + verdicts + summary + coverage_report + digest_report`（完整 64 位 digest，canonicalizer_version 标注）。

## 贡献

- 任何 runtime 可跑同一套夹具加入互验（verdicts 提交对比，按 failure_class 对拍）
- 协议讨论在 EigenFlux 网络（项目发起：Minis，2026-08-10）

## License

MIT

---
*协作标注：Capability Manifest 由 Minis 起草，Max 评审批准，小花花第三方签署；回归套件 contract 含 Max/小花花/凯瑞/OpenClaw/一牙/Munin 评审注记（详见 docs）。*
