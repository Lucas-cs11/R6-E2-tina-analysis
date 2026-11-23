# R6-04 故障后截止与 H_A 端点（临时）

**`PASS_PROVISIONAL_R6_04_PARTIAL_NOT_PHASE_GATE`**

6/6 用例通过：`τ_c-τ_f < B_c`、`= B_c`、`> B_c`，未完成但已过截止，短前缀未到期，以及 `τ_f+B_c=H_A` 的合法端点完成。

3/3 真实变异检出：等号误判违反、短前缀误判违反、H_A 端点先截断。

证据：`runs/g2_r604/results.csv`、`summary.json`、`mutations/`。不覆盖一般 H_A 截断扫描或混合状态类分割，不关闭 G2。
