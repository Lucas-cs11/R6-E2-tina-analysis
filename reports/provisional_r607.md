# R6-07 隐含/显式位置重置（临时）

**`PASS_PROVISIONAL_R6_07_PARTIAL_NOT_PHASE_GATE`**

两套独立实现（subject 区间分类重置、oracle 集合差重置），5/5 用例一致。

## 覆盖场景

- 隐含重置：消耗位置中未显式声明的全部隐式清零。
- 显式重置：仅声明的显式位置清零，其余消耗位置保留。
- 重置未消耗：显式重置包含未消耗位置，返回非法。
- 未使能：transition 前条件不满足，返回非法。
- 未知 transition：返回非法。

## 真实变异（3/3 检出）

1. `M_RESET_ALL_CONSUMED`：全部消耗位置被重置（忽略显式声明）。
2. `M_IGNORE_EXPLICIT`：显式重置被忽略，全部消耗位置被重置。
3. `M_ALLOW_UNCONSUMED_RESET`：允许重置未消耗位置。

## 证据

- `runs/g2_r607/results.csv`
- `runs/g2_r607/summary.json`
- `runs/g2_r607/mutations/*/mutation.patch`

不覆盖一般 reset arc 语义或完整 R6-07 套件；不关闭 G2。
