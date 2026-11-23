# R6-02 同发故障/完成与窗口端点（部分）

**状态：`PASS_PROVISIONAL_R6_02_PARTIAL_NOT_PHASE_GATE`**

两套独立实现（subject 逐事件求首个 pre-completion 故障；oracle 先收集再取最小）对 5 个边界用例一致。

## 覆盖

- 同一变迁首次故障+首次完成：τ_f=τ_c，故障后时长 0，不判违规 → H1。
- 首次故障 < Hψ → H1。
- 首次故障 = Hψ（闭端点）→ H1。
- 首次故障 > Hψ → H0。
- 完成后新故障（time ≤ Hψ 但晚于首次完成）→ H0，不计入本次。

## 真实源码变异（3/3 检出）

1. 端点改为严格 `<`：τ_f=Hψ 被误判 H0。
2. 移除 `time<=first_completion`：完成后新故障被计为首次故障 → H1。
3. 零时长被改为 1：同发故障/完成被误标违反。

## 证据

- `runs/g2_r602/results.csv`
- `runs/g2_r602/summary.json`
- `runs/g2_r602/mutations/*/mutation.patch`

## 未覆盖

- 完整 SCG 引擎、混合状态类精确分割（R6-05）、B_c 全窗扫（R6-04）不在此组件。
