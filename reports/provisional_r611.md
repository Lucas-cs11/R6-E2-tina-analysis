# R6-11 Bayes 误差/覆盖/粗化（临时）

**`PASS_PROVISIONAL_R6_11_PARTIAL_NOT_PHASE_GATE`**

两套独立实现（subject 精确有理、oracle 直接求和），4/4 用例一致。

## 覆盖场景

- 精细不可靠：Bayes 误差 1/10，覆盖率 1。
- 精细可靠：Bayes 误差 1/10，覆盖率 1。
- 粗化 A：Bayes 误差 1/10→1/2，覆盖率 1→0。
- 粗化 B：Bayes 误差 1/10→1/10，覆盖率 1/2→1。

## 真实变异（3/3 检出）

1. `M_BAYES_MAX`：Bayes 误差用 max 而非 min。
2. `M_COVERAGE_WRONG_POSTERIOR`：覆盖率用后验 min 而非 max。
3. `M_COARSEN_MAP_WRONG`：粗化映射塌缩到单键。

## 证据

- `runs/g2_r611/results.csv`
- `runs/g2_r611/summary.json`
- `runs/g2_r611/mutations/*/mutation.patch`

不覆盖连续分布或完整 R6-11 套件；不关闭 G2。
