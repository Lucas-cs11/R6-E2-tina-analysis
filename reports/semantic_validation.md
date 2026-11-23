# R6-E2 语义对齐验证（PyScrew 48 候选）

## 结论

48/48 比较候选在获得“物理类别→故障发射变迁→首次完成/外部观测”的可验证绑定之前，**不能认证为严格 LSTPN 故障事件证书**；只允许经验分类分析。

## 依据

- `chapter6/physical_to_tpn_mapping.csv` 给出四阶段控制器 TPN 模板：
  - `P0 -> (t_find/t_thread/t_pretight/t_final)` 链（N/F 副本）
  - 通用故障变迁 `t_init_F` / `t_init_N`（`[0,0]`）
  - 完成标识 `P_COMPLETE`
- 该映射把**物理要素/阶段**映射到 TPN 模板元素，但：
  1. 没有把 24 个物理变化类别（如 `101_deformed-thread`）各自绑定到具体故障发射事件；
  2. 没有提供控制类 `001_control-group` 的故障事件定义；
  3. 没有逐类别“首次完成事件、外部完成通道、故障历史”三者可验证对齐。
- 因此 `t_init_F` 只能当作模板占位，不能证明每个类别的故障历史满足第五章跨层对齐条件。

## 48 候选状态

- `certifiability = NOT_CERTIFIABLE_UNTIL_CLASS_FAULT_SEMANTICS`
- `fault_event_mapping = GENERIC_TEMPLATE_ONLY_NO_CLASS_BINDING`
- `control_fault_mapping = MISSING`
- `allowed_analysis = EMPIRICAL_CLASSIFICATION_ONLY`

证据：`scope/comparison_candidates_48.csv`、`scope/comparison_candidates_48_summary.json`。

## 要求

主理论助手或领域定义须提供逐类别故障语义，之后实验 Agent 才能把任何候选标为 `CERTIFIABLE`。在此之前的任何风险证书都不得声称 48 个严格故障事件证书。
