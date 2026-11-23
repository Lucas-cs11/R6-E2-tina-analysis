# R6-E2 第 17 轮只读安全审查

审查范围：`runs/review_round17.diff`，以及新增 R6-05/R6-06 subject、independent oracle、运行器、真实源码变异，`tests/final_verify_r6_e2.py` 和 `tests/run_negative_controls.py` 的当前实际内容。本报告仅记录高置信安全问题，不构成 G5 独立签署或完整闭合结论。

## Finding 1 — 原始清单路径穿越及重复目标可将同一文件伪装成 5000 条原始证据

- severity: HIGH
- confidence: HIGH
- file: `tests/final_verify_r6_e2.py`
- line: 59-75
- 理由: `physical_class` 和 `file_name` 直接拼入 `raw / r['physical_class'] / r['file_name']`，未拒绝绝对路径、`..`、非规范路径或符号链接。绝对路径组件会抛弃既定 `raw_root/raw_json` 前缀。清单也没有要求 `(physical_class, file_name)` 或 `run_id` 唯一。伪造清单只需维持 5000 行、2500 个 workpiece 且各自有 left/right 两行，即可让全部行重复指向同一个已知文件并填写该文件的真实 SHA-256；`checked == 5000`、`mismatched == 0` 后得到 `FULL_RAW_REPRODUCIBLE`，并未证明 5000 个不同原始样本存在。
- 修复建议: 对两个路径字段执行严格的规范相对路径校验；从可信原始根目录 fd 逐组件使用 `O_NOFOLLOW` 打开并 `fstat`，拒绝根外解析和链接；强制原始文件身份、`run_id`、workpiece/location 映射唯一，并核对冻结的类别、source group 与预期数据集身份。增加绝对路径、`..`、父级链接及 5000 行重复同一文件的负测。

## Finding 2 — 新增组件可由空账本或自报状态通过最终验收，语义字段和变异结果未重算

- severity: HIGH
- confidence: HIGH
- file: `tests/final_verify_r6_e2.py`
- line: 94-118
- 理由: `component_specs` 为 R6-05 配置的 `actual`、为 R6-06 配置的 `subject_verdict` 在循环中被 `_` 丢弃。验收器只读取 CSV 的 `status` 和 JSON 的 `status/cases/mutations[].detected`，不读取逐项 subject/oracle JSON，也不重新执行实现或变异。把任一新增组件的 `results.csv` 留为仅表头，并提供 `{"status":"PASS","cases":0,"mutations":[]}`，即可满足全部组件条件；也可保留非空行而任意篡改 R6-05 的 `actual` 或 R6-06 的 `subject_verdict/oracle_verdict`。`tests/run_negative_controls.py:56-68` 虽复制新组件目录，却只翻转 R6-03 的 `status`，因此无法发现这些绕过。
- 修复建议: 固定每个组件的用例 ID、预期数量和临时阶段标记，拒绝零用例及未知用例；从逐项原始输出重新计算 subject/oracle 一致性和语义字段，验证变异源码/补丁与当前源码的绑定并重跑变异，而非采信 `detected: true`。为 R6-05/R6-06 分别增加空 CSV、伪造 summary、翻转 actual/verdict、伪造 mutation detected 的负测。

## Finding 3 — 107520 个模型的 SHA-256 仅检查字符串长度，未绑定模型内容

- severity: HIGH
- confidence: HIGH
- file: `tests/final_verify_r6_e2.py`
- line: 83-92
- 理由: 对生成总体的每个候选，验收器只要求 `model_sha256` 长度为 64，既不检查十六进制格式，也不重新生成规范模型或读取模型文件重算摘要。保留候选 ID 集合并将全部摘要改成 64 个 `0`，同时自报 `GENERATED_STRUCTURE_PASS` 和空 `structural_issues`，该段验收仍可通过；当前负测没有覆盖摘要或结构状态的伪造。
- 修复建议: 将每个摘要绑定到持久化的规范模型及明确的 canonicalization 版本，逐一重算 SHA-256；或由验收器从冻结参数重新运行生成器和结构检查。增加任意 64 字符、全零摘要及自报结构 PASS 的负测。

## Finding 4 — 新增 R6-05/R6-06 的 TeX 哈希是自报常量，没有与实际冻结 TeX 绑定

- severity: MEDIUM
- confidence: HIGH
- file: `implementations/subject/r605.py`, `implementations/subject/r606.py`, `oracles/independent/r605_reference.py`, `oracles/independent/r606_reference.py`, `tests/final_verify_r6_e2.py`
- line: 6-7（四个实现文件）；94-118（最终验收器）
- 理由: 四个实现分别硬编码相同的 `TEX` 值并输出 `tex_sha256`。R6-05 的 subject/oracle 整体相等检查和 R6-06 的有限字段比较都不能证明该值属于实际 TeX；最终验收器也不读取 `baseline_readonly/example_revised_theory_v2_theory_round6_candidate.tex`、`contracts/experiment_scope_frozen.json` 的 `theory_tex_sha256` 或新增逐项 JSON。实际 TeX 被替换，或四个常量同时改成伪造值，现有验收与负测仍可 PASS。
- 修复建议: 在最终验收器中重算冻结 TeX 的 SHA-256，将其与冻结合同及每个新增用例的 subject/oracle 输出逐字比较；不要以多个实现共享常量作为独立绑定证据。增加 TeX 内容变化和输出哈希变化的负测。
