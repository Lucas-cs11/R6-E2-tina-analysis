# R6-E2 全量主实验、经典基线与数学接口整改

## 状态

**`PARTIAL_VALIDATED_NOT_CLOSED`**

本轮完成 R6-E1 审计的三个强制前置（部分），未执行 G2—G5。

## 已完成

- G0-1：八轴 143,360 形式候选全枚举（107,520 合法 / 35,840 非法）；合法格实际生成/结构验证已完成：**107,520/107,520 PASS，0 错误，0 重复**（`results/all_population_results.csv`）。
- G0-2：PyScrew `--raw-root` 可移植清单，5000/2500/25/50 实测可重放；48 候选语义对齐已核实为 `NOT_CERTIFIABLE`（仅经验分类）。
- G2（部分）：R6-01 3/3、R6-02 5/5、R6-03 3/3、R6-04 6/6、R6-05 3/3、R6-06 6/6、R6-10 8/8；合计 36 个真实变异均检出；均非正式阶段 PASS。
- G1：R6-08 联合区间可行性纠偏，20/20 边界、5/5 真实源码变异；宽松上界取交、只有下界越界才矛盾。
- G4 敏感性：逻辑 1620 模型已实际生成并结构验证（54×10×3）；概率 a4 21 点全 PENDING_SPEC（R6-11 只验证离散分布算法，未独立计算连续模型值）；567 矩阵与判定 135 全 `PENDING_SPEC`（无阈值，骨架）。
- G3 基线：历史 52 模型同题适配器已验证 36 个生成模型结构等价；16 个 micro 无生成参数；18 项外部 L/P 基线仍 `NOT_AVAILABLE`。
- 最终验收器：从原始 CSV/文件重算计数与 SHA；3 个篡改负测全部失败、基线通过。

## 关键文件

- `contracts/experiment_scope_frozen.json`
- `contracts/math_interface_round6_frozen.md`
- `scope/protocol_lineage.md`
- `scope/generator_candidate_universe_full.csv`（143,360 行）
- `scope/generator_candidate_universe_summary.json`
- `scope/pyscrew_raw_manifest.csv`（5,000 行）
- `scope/comparison_candidates_48.csv`
- `reports/semantic_validation.md`
- `baselines/baseline_registry.csv`
- `runs/g1_r608/results.csv`、`runs/g1_r608/summary.json`
- `runs/negative_controls/negative_controls.json`
- `reports/provisional_r601.md`
- `reports/provisional_r607.md`
- `reports/provisional_r611.md`
- `reports/provisional_r602.md`
- `reports/provisional_r603.md`
- `reports/provisional_r604.md`
- `reports/provisional_r605.md`
- `reports/provisional_r606.md`
- `reports/provisional_r608_module.md`
- `reports/provisional_r609.md`
- `reports/provisional_r612.md`
- `reports/provisional_r613.md`
- `reports/provisional_r610.md`
- `runs/g2_r602/results.csv`
- `reports/full_scope_audit.md`、`reports/remaining_blockers.md`

## 复现

```bash
cd theory_validation/R6_E2
python3 tests/enumerate_generator_universe.py
python3 chapter6/build_population_portable.py --raw-root /path/to/pyscrew
python3 tests/run_g1_r608.py
python3 tests/run_negative_controls.py
python3 tests/final_verify_r6_e2.py --raw-root /path/to/pyscrew
```

## 边界

- 不修改论文/TeX/定理/证明。
- 不宣称四实现新引擎、全量实验、敏感性或独立终验已闭合。
- 原始 5000 JSON 不入包，无 raw 时等级为 `SOURCE_MANIFEST_AUDITED_NOT_RAW_VERIFIED`。
