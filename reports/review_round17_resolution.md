# 第17轮审查整改闭环

## 审查发现

- security-reviewer：3 项 HIGH（原始路径穿越/重复计数、组件空账本/自报PASS、模型SHA仅验长度）+1 MEDIUM（TeX哈希硬编码未重算）。
- architecture-reviewer：1 项 HIGH（R6-06 仅凭 `search_complete=True` 即返回 DECIDED/1）+1 MEDIUM（终验丢弃语义字段不核原始JSON）。

## 复现确认

`runs/review_exploits/exploit_results.json`：4 个旧 exploit（绝对路径+重复计数、空组件、缺变异补丁、全零模型SHA）在旧验收器全部 `unexpected_accept=true`。

## 整改

1. `tests/final_verify_r6_e2.py` 全面强化：原始路径去重且必须限制在 raw-root、组件非空且绑定原始subject/oracle JSON与变异补丁工件、模型SHA必须匹配一次生成器重放（107520 个）、TeX哈希现场重算。
2. R6-06 subject/oracle 改为 fail-closed：无见证时 `PERP`，不由 `search_complete` 布尔标志推断无歧义。冻结TeX第1354行印证该假设不成立。

## 验证

- 旧 exploit 在新验收器全部 `unexpected_accept=false`（见负测 `runs/negative_controls/negative_controls.json`）。
- 新负测 10 项（含 4 项新 exploit + 6 项原有）：9 篡改全部拒绝、未修改基线通过。
- 全量重验 `runs/final_verify_postfix.stdout.json`：`PASS`，107520 模型哈希重放绑定、5000 原始 SHA、TeX 重算、6 组件 15 变异全检。

## 状态

这是**证据完整性修复**，不改理论合同、不提升任何阶段结论；总体仍 `PARTIAL_VALIDATED_NOT_CLOSED`，G7 未闭合。
