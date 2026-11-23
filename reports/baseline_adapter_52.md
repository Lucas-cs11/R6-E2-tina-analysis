# G3 经典基线同题适配（第一步：历史 52 模型）

**`ADAPTER_VALIDATED`**

## 范围

- 历史 52 个模型（36 个协议生成 + 16 个微型）。
- 同题适配器把 `freeze.json` 中的生成参数映射到当前重建的 TPN 数据层，重新生成模型并做结构等价验证（L/H/places/transitions 与历史逐行表一致）。

## 结果

- 36 个生成模型：`ADAPTER_VALIDATED`，结构等价，SHA-256 已记录。
- 16 个微型模型：`NOT_AVAILABLE_PARAMS_ONLY`（freeze 中无生成参数，无法重建）。
- 52/52 唯一，无重复。

## 状态

- 这是**结构层同题适配**，不是历史四实现重跑，不是逻辑判定。
- 18 项外部 L/P 基线（L-01—L-10、P-01—P-08）仍 `NOT_AVAILABLE`/`UNASSESSED`，无可运行实现。

## 证据

- `results/baseline_adapter_52.csv`
- 终验含适配器检查：`runs/final_verify_with_adapter.stdout.json`

不关闭 G3，G7 未闭合。
