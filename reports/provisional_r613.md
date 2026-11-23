# R6-13 传感器延迟（临时）

**`PASS_PROVISIONAL_R6_13_PARTIAL_NOT_PHASE_GATE`**

两套独立实现（subject 排序后比对、oracle 成对验证），5/5 用例一致。

## 覆盖场景

- 精确延迟：观测时刻 = 真实时刻 + 延迟。
- 延迟不匹配：观测时刻与真实时刻+延迟不符。
- 计数不匹配：真实事件数与观测事件数不同。
- 零延迟：观测时刻等于真实时刻。
- 负延迟：观测时刻早于真实时刻（允许）。

## 真实变异（3/3 检出）

1. `M_IGNORE_DELAY`：忽略延迟，直接比较真实时刻与观测时刻。
2. `M_ALLOW_COUNT_MISMATCH`：允许计数不匹配。
3. `M_DROP_NEGATIVE_DELAY`：负延迟被当作绝对值，负延迟用例被误判。

## 证据

- `runs/g2_r613/results.csv`
- `runs/g2_r613/summary.json`
- `runs/g2_r613/mutations/*/mutation.patch`

不覆盖一般传感器融合或完整 R6-13 套件；不关闭 G2。
