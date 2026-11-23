# R6-05 混合状态类精确分割（临时）

**`PASS_PROVISIONAL_R6_05_PARTIAL_NOT_PHASE_GATE`**

subject 使用精确有理 Fourier–Motzkin；oracle 独立枚举二维约束边交点，不共享实现。

3/3 用例通过：

- 混合类：同时保留 `θ_f>B_c` 违规片和 `θ_f≤B_c` 合规片；合规首次完成见证保留。
- 全合规：违规片为空，不输出未决。
- 全违规：合规片为空。

严格违规下界单独标记，未用闭包边界冒充违规见证。2/2 真实变异检出：剪掉整个混合类、丢弃合规完成见证。

证据：`runs/g2_r605/results.csv`、逐项 JSON、`mutations/`。不覆盖一般维数 oracle 或完整 SCG。
