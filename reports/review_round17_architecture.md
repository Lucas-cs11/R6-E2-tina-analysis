# R6-E2 第17轮架构 / 数学接口审查

## 范围与结论

审查 `runs/review_round17.diff` 及当前实际源文件，覆盖 R6-05 Fourier–Motzkin 与二维顶点 oracle、严格不等式、R6-06 观测投影与搜索完整性、终验组件接入和负测。

发现 **2 项高置信问题**：R6-06 可在缺少完整搜索证明时错误返回性质 `1`，终验又只核对账本状态而无法识别该语义错误。R6-05 在当前有限二维盒约束测试域内未发现高置信计算错误；其 subject 与 oracle 使用不同可行域算法，未共享求解代码。

本报告不是 G5 独立签署，也不表示 R6-E2 完整闭合。

## Findings

### F-01：R6-06 将输入布尔值当作完整搜索证明，subject 与 oracle 会共同产生错误 `DECIDED/1`

- **severity:** HIGH
- **confidence:** HIGH
- **file/line:** `implementations/subject/r606.py:32-45`；`oracles/independent/r606_reference.py:30-42`；`tests/run_g2_r606.py:27-37,53-58`；对应冻结理论接口 `baseline_readonly/example_revised_theory_v2_theory_round6_candidate.tex:1354,1361-1388,1401-1412`。

**理由：**

两个实现都只枚举 `data['paths']` 中当前给出的路径；未发现见证后，只要 `data.search_complete` 为真就返回 `verdict='1'` 和 `status='DECIDED'`。二者既不构造 SCG/TCSCG，也不核对候选全集、未解析前沿或搜索覆盖记录。oracle 重复使用同一个输入标志，因此与 subject 一致不能形成独立正确性证据。

冻结理论接口明确规定：返回 `1` 需要图、同步器、候选路径展开和求解等必要构造完整；并且“**仅有布尔完整性标志本身不称为独立证明证书**”。当前实现没有保存或核验理论接口所述完整搜索记录。

测试把该错误固化为 PASS：`data(..., complete=True)` 只是写入布尔值，`FULL_WORD_DIFFERENT` 用两条手工路径即期待 `1`；粗化测试的 fine 侧也同样期待 `1`。在实际完整路径集合还包含另一条与正常路径等观测的故障路径时，只要该故障路径没有放进 `paths`，两个实现仍会共同返回 `1`。这属于共享假设造成的错误 PASS，而非独立交叉验证。

`summary.json` 虽声明 `complete SCG construction` 未覆盖，但输出仍使用具有性质判定语义的 `DECIDED/1`，范围声明没有消除接口误判。

**建议：**

1. 在没有可核验完整搜索证据时，无见证分支只返回 `PERP/UNRESOLVED`；真实见证支持的 `0` 可保留。
2. 若 `1` 仅表示给定样本路径彼此可区分，改用独立的样本级结果字段，不占用逻辑性质 `verdict=1`。
3. 为完整性建立可核查证据接口，至少绑定完整候选/路径清单、各搜索阶段完成状态、空未解析前沿及输入模型身份，并由独立组件验证覆盖关系。
4. 增加负测：在已有正常路径之外省略一个等观测故障路径，同时设置 `search_complete=True`；当前两个实现都会错误返回 `1`，修复后不得将该输入当作完整搜索证书。

### F-02：终验对 R6-05/R6-06 只有 CSV 账本覆盖，没有原始结果或语义覆盖

- **severity:** MEDIUM
- **confidence:** HIGH
- **file/line:** `tests/final_verify_r6_e2.py:94-118`；`tests/run_negative_controls.py:56-69`。

**理由：**

`component_specs` 为 R6-05 配置了 `actual`、为 R6-06 配置了 `subject_verdict`，但循环将该第二字段绑定为 `_` 后完全弃用。终验实际只检查：

- CSV 每行的 `status` 是否为 `PASS`；
- CSV 行数是否等于摘要自报的 `cases`；
- 摘要自报的 `mutations` 是否全部标记 `detected=true`；
- 摘要自报的 `status` 是否为 `PASS`。

终验不读取逐项 `*.subject.json`、`*.oracle.json`，不比较 `expected/actual` 或 `expected/subject_verdict/oracle_verdict`，不检查 `errors` 列，也不验证变异源码、补丁和观测结果。因此，即使 R6-06 的 `FULL_WORD_DIFFERENT.subject.json` 已包含 F-01 所述无完整证明的 `DECIDED/1`，只要 CSV 写成 PASS，终验仍给组件通过。逐项 JSON 缺失或与 CSV 矛盾、oracle mismatch 被写入 `errors` 但状态未改，也不会被终验识别。

组件负测虽复制了 `g2_r605` 和 `g2_r606`，实际只翻转 `g2_r603` 的一行状态；没有覆盖新组件的原始结果缺失、语义字段不一致或 oracle 分歧。

**建议：**

1. 使用已配置的第二字段，逐案例核对预期值、subject、oracle 和 CSV 状态，并要求 `errors` 为空。
2. 将 CSV 与逐项原始 JSON 绑定，固定必需 case ID 和数量；对变异结果核对 `detected` 与原始观测，而非只读摘要布尔值。
3. 增加 R6-05/R6-06 专项负测：原始 JSON 缺失、subject/oracle 分歧、语义字段与 CSV 不一致、摘要虚报变异检出均必须使终验 FAIL。

## R6-05 专项核对（未形成 finding）

- `implementations/subject/r605.py:20-40` 的异号约束配对公式与 Fourier–Motzkin 投影一致；`oracles/independent/r605_reference.py:26-37` 改用二维边界直线交点枚举，两者没有相互导入或共享求解函数。
- 当前测试输入为两个变量的有限上下界盒加线性约束，非空闭可行域具有顶点，因此 oracle 以顶点非空判断闭区域可行在当前测试域内成立；一般维数和无界/开放输入未被该结论覆盖。
- `implementations/subject/r605.py:78-89` 先构造含 `θ_f=B_c` 的闭包，再以投影上界严格大于 `B_c` 判定违规片；`oracles/independent/r605_reference.py:40-58` 对闭区域顶点再执行 `p[var] > B_c`。在当前有界二维域内，两者均不会把仅位于等号边界的点计作严格违规见证。
- 现有 `ALL_COMPLIANT` 覆盖整体上界等于 `B_c` 的等号情形。未发现需要新增高置信 finding 的 R6-05 共享计算错误。
