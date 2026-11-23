# G4 敏感性：逻辑 1620 模型实际生成（第一步）

**`PASS_GENERATED_STRUCTURE`**

## 范围

- 54 论文最小子域格 × seed 0..9 × WIP 1..3 = **1620 个模型**。
- 每个模型实际调用生成器、结构验证、规范化 SHA-256。
- 结果：`results/sensitivity_logical_1620_results.csv`（1620 行，全 `GENERATED_STRUCTURE_PASS`，0 错误，0 重复）。

## 状态

- 1620/1620 唯一、结构验证通过。
- 这是**生成/结构层**，不是四实现诊断执行，不是逻辑判定。

## 边界

- 概率 567（a4 网格 × 分布 × 根权重 × 量化）与判定 135（pi1 × ε × δ × γ）仍 `PENDING_SPEC`，待理论负责人给出具体分布/权重/量化取值。
- 若叠加 L/H 三档，最多 14580 模型—规格格、4 实现 58320 次调用，仅敏感性子域。

## 证据

- `results/sensitivity_logical_1620_results.csv`
- `results/sensitivity_logical_1620_summary.json`
- 终验含敏感性检查：`runs/final_verify_with_sens1620.stdout.json`
