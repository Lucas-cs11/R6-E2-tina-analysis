# 逻辑生成协议谱系

## 冻结材料

- `scope/freeze.json`：R4 D1 冻结任务列表，52 主模型（16 微模型 + 36 生成点）×4 方法。
- `scope/fullscale_protocol_v1.yaml`：旧协议。
- `scope/fullscale_protocol_corrected.yaml`：修正参考基线，状态 `fullscale_corrected_baseline`；声明 `param_slice: 3`、`n_seeds: 15`，README 记载为 36,450 实例历史网格。
- `scope/rmt_fms_generator.py`：RMT/FMS 生成器原文；SHA-256 `4ab74687b1593bd002f07b9b9af99259f822773db6ff060b732d2856fc3892fb`。

## 两个不可互相替代的集合

1. 论文最小矩阵：`m∈{2,3,4}×j∈{1,2}×u∈{0.1,0.3,0.5}×w∈{0.5,1.0,1.5}` = 54 格；另有 16 微模型独立边界集合。
2. 八轴形式乘积：7×5×4×4×4×4×4×4 = 143,360 格，来自 `fullscale_protocol_corrected.yaml` 的 machine/part/ops/wip/u/fault/w/adjustable 轴。

## 静态合法性规则（运行前冻结）

见 `scope/model_validity_rules.json`。唯一导致非法的是 `fault_locations > machine_counts`（无法在更多不同机器上放置故障）。

- 全候选：143,360
- `VALID_BY_FROZEN_RULE`：107,520
- `INVALID_BY_FROZEN_RULE`：35,840

## PROVENANCE_UNRESOLVED

- 历史 52 主模型为何只执行 36 个生成点、未覆盖 54 或八轴域：现有材料无证据，标 `PROVENANCE_UNRESOLVED`。
- 36 个生成模型原始字节缺失，重建模型身份只能标 `RECONSTRUCTED`，不能写成原模型 SHA。
- 最终研究域（54 vs 143360）的数学/写作裁定由主理论助手完成；实验 Agent 只提交可核查的轴、约束与候选清单。

## 门槛结论

G0-1 的“全候选入清单”已满足（143,360 行，无缺漏重复）；但尚未逐合法格实际生成 PN（后续阶段），故 G0-1 不闭合。
