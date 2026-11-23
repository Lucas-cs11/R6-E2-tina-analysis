# G4 概率敏感性完整报告

## 模型

Y0 = max(X3, X5)，Y1 = max(X4, X5)；X3~U[2,4]，X5~U[1,3]，X4~U[a4,5]；a4 ∈ [3,4]。

## 精确解析结果

Pe* = (4-a4)²/(4·(5-a4))，Gamma = 0（后验=0.5 < 0.85）。

| a4 | Pe* | Gamma |
|---|---|---|
| 3 | 1/8 | 0 |
| 3.5 | 1/24 | 0 |
| 4 | 0 | 0 |

## 已完成的敏感性分析

1. **a4 变化**：21 点网格，Pe 单调递减。
2. **宽度因子**：X4~U[a4,5w]，Pe 随 w 增大而减小。
3. **观测量化**：Y 离散化为桶，Pe 随桶数增加收敛到连续值。
4. **三维联合**：a4 × 宽度 × 桶数，强交互效应。
5. **完整 567 矩阵**：21 a4 × 3 宽 × 3 桶 × 3 先验。
6. **支持层**：零测度边界保留，概率层零质量。
7. **跨层对齐**：逻辑 VER 不蕴含概率 1。
8. **历史保持**：q0+q1=1 互补收紧。
9. **风险区间**：不确定 a4 的 Pe 上下界。
10. **回退区间**：精确值在平凡回退 [0,1/2] 内。

## 关键发现

- 连续模型 Gamma=0 与离散模型 Gamma=1/2 的差异源于离散化。
- 支持层和概率层分离：支持层保留零测度边界，概率层给零质量。
- 逻辑层 VER 不蕴含概率层 1，两层需分别认证。

## 文件清单

- `results/probability_a4_21points.csv`：21 点精确 Pe/Gamma
- `results/probability_567_full.csv`：完整 567 矩阵
- `results/probability_a4_sensitivity.csv`：a4 敏感性
- `results/probability_a4_width_sensitivity.csv`：宽度敏感性
- `results/probability_a4_quantization.csv`：量化敏感性
- `results/probability_a4_multi_sensitivity.csv`：多变量敏感性
- `results/probability_a4_3d_sensitivity.csv`：三维敏感性
- `results/probability_support_layer_analysis.json`：支持层
- `results/probability_cross_layer_alignment.json`：跨层对齐
- `results/probability_history_preservation.json`：历史保持
- `results/probability_risk_interval.json`：风险区间
- `results/probability_fallback_interval.json`：回退区间
