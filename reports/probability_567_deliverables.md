# G4 概率 567 矩阵最终交付清单

## 核心交付物

| 文件 | 描述 | 状态 |
|---|---|---|
| `results/probability_a4_21points.csv` | 21 点精确 Pe/Gamma | EXACT_ANALYTIC |
| `results/probability_567_analytic.csv` | 解析 567 矩阵 | EXACT_ANALYTIC |
| `results/probability_567_full.csv` | 数值 567 矩阵（16 桶） | NUMERIC |
| `results/probability_567_1024.csv` | 数值 567 子集（1024 桶） | NUMERIC |
| `results/probability_567_convergence.csv` | 收敛验证 | PASS |
| `results/probability_567_consistency.json` | 一致性验证 | PASS |
| `results/probability_567_performance.json` | 性能总结 | PASS |
| `results/probability_files_integrity.json` | 文件完整性 | PASS |

## 敏感性分析

| 文件 | 描述 |
|---|---|
| `results/probability_a4_sensitivity.csv` | a4 变化 |
| `results/probability_a4_width_sensitivity.csv` | 宽度因子 |
| `results/probability_a4_quantization.csv` | 观测量化 |
| `results/probability_a4_multi_sensitivity.csv` | 多变量 |
| `results/probability_a4_3d_sensitivity.csv` | 三维联合 |

## 语义验证

| 文件 | 描述 |
|---|---|
| `results/probability_support_layer_analysis.json` | 支持层 |
| `results/probability_cross_layer_alignment.json` | 跨层对齐 |
| `results/probability_history_preservation.json` | 历史保持 |
| `results/probability_risk_interval.json` | 风险区间 |
| `results/probability_fallback_interval.json` | 回退区间 |
| `results/probability_age_semantics.json` | 年龄语义 |

## 报告

| 文件 | 描述 |
|---|---|
| `reports/probability_sensitivity_full.md` | 敏感性完整报告 |
| `reports/probability_567_full.md` | 567 完整报告 |

## 关键结论

- Pe* = (4-a4)²/(4·(5w-a4))，Gamma=0（连续模型）。
- 解析公式远比数值积分高效。
- 支持层和概率层分离，逻辑层 VER 不蕴含概率层 1。
