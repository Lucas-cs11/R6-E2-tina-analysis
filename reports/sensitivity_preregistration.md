# G4 敏感性矩阵预注册（未执行）

## 逻辑

- `results/sensitivity_logical_1620.csv`：54 基础格 × seed 0..9 × WIP 1..3 = 1620 行，全部 `NOT_EXECUTED`。
- 若叠加 L/H 三档，最多 14580 模型—规格格、4 实现 58320 次调用；仅敏感性子域，不冒充八轴全集。

## 概率

- `results/sensitivity_probability_567.csv`：a4=3+k/20 (k=0..20) × 3 分布 × 3 根权重 × 3 观测量化 = 567 行，`PENDING_SPEC`。
- 具体分布/权重/量化取值待理论负责人给出，未虚造数值。

## 判定规格

- `results/sensitivity_spec_135.csv`：pi1 五档 × epsilon/delta/gamma 各三档 = 135 行，`PENDING_SPEC`。

这些只是预注册骨架，不是任何执行结果或性能结论。
