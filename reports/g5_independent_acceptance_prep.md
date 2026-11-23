# R6-E2 G5 独立终验准备：证据清单与待核清单

## 当前状态

总体：`PARTIAL_VALIDATED_NOT_CLOSED`。所有验证为 Lead 自验，G5 独立签署未执行。

## 已完成证据（Lead 自验）

| 阶段 | 状态 | 证据 |
|---|---|---|
| G0 候选枚举 | 143,360 全枚举，107,520 合法 | `scope/generator_candidate_universe_full.csv` |
| G0 实际生成 | 107,520/107,520 结构 PASS | `results/all_population_results.csv` |
| G0 PyScrew | 5,000 SHA 全重算 | `scope/pyscrew_raw_manifest.csv` |
| G0 48 候选 | 语义不可认证已核实 | `scope/comparison_candidates_48.csv` |
| G1 R6-08 纠偏 | 20/20、5/5 变异 | `runs/g1_r608/` |
| G2 R6-01—13 | 13 组件、36 变异全检出 | `runs/g2_r*/` |
| G3 适配器 | 52 模型，36 验证 | `results/baseline_adapter_52.csv` |
| G4 敏感性 | 1620 生成结构 PASS | `results/sensitivity_logical_1620_results.csv` |
| 防篡改终验 | 10 负测全拒绝 | `runs/negative_controls/negative_controls.json` |
| 模型哈希重放 | 107,520 重放绑定 | `results/model_hash_replay.csv` |

## 待核清单（G5 独立签署需逐项核验）

1. **G0 生成器正确性**：`rmt_fms_generator.py` 是否忠实实现协议？历史 52×4 模型结构是否与 freeze 参数一致？
2. **G1 纠偏完整性**：R6-08 的 Q 上界相交规则是否覆盖所有联合可行性情况？独立 oracle 是否真正独立？
3. **G2 组件覆盖度**：13 个组件是否覆盖 R6-01—R6-13 的所有边界？变异是否足够尖锐？
4. **G3 适配器等价性**：当前引擎生成的模型与历史模型是否真正同题？L/H/places/transitions 匹配是否充分？
5. **G4 敏感性代表性**：1620 模型是否覆盖 54 格的所有参数组合？结构验证是否足够？
6. **防篡改终验完备性**：10 个负测是否覆盖所有篡改路径？终验器是否有遗漏？
7. **原始数据可移植性**：`--raw-root` 是否正确重放 5,000 JSON？SHA 是否全部匹配？
8. **TeX 哈希绑定**：`baseline_readonly/example_revised_theory_v2_theory_round6_candidate.tex` 是否与冻结 SHA `a4196145...` 一致？

## 未执行/不可执行

- G3 外部基线：TINA 下载中（用户手动），其余 17 项仍 `NOT_AVAILABLE`。
- G4 概率 567：待 D1/D2/D3 分布规格 + 连续分布引擎。
- G4 判定 135：待 pi1/ε/δ/γ 阈值规格。
- G5 独立签署：未执行。

## 建议 G5 流程

1. 独立审查者从 `R6_E2_complete_workspace.zip` 解压，不复用 Lead 工作区。
2. 逐项核验"待核清单"。
3. 跑 `tests/final_verify_r6_e2.py --raw-root /path/to/pyscrew` 独立重放。
4. 跑 `tests/run_negative_controls.py` 独立验证负测。
5. 签署 `reports/independent_acceptance.md`。
