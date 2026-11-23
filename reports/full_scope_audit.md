# R6-E2 范围与前置整改审计

审计日期：2026-11-22  
结论：**`PARTIAL_VALIDATED_NOT_CLOSED`**。G0/G1 的强制前置有实质进展，但 G0-1 实际生成、G0-2 语义对齐、G2—G5 未完成。

## G0-1 逻辑生成候选域

- 冻结协议、生成器、`fullscale_protocol_v1/corrected.yaml`、`freeze.json`。
- 八轴形式候选：**143,360 全部入清单**，无缺漏重复。
- 静态合法性（运行前冻结）：`fault_locations <= machine_counts` 等 8 条规则。
- `VALID_BY_FROZEN_RULE`：107,520；`INVALID_BY_FROZEN_RULE`：35,840。
- 54 格论文最小子域单独记录，不冒充八轴域。
- 生成器 SHA-256：`4ab74687b1593bd002f07b9b9af99259f822773db6ff060b732d2856fc3892fb`。
- 已逐个合法格实际生成 PN：**107,520/107,520 结构验证 PASS，0 错误，0 重复**；这是生成/结构层，不是四实现执行。

## G0-2 PyScrew 可移植来源

- 入口改为 `--raw-root`，无本机绝对路径硬编码。
- 以 `/Users/lucas/Downloads/results1005/pyscrew` 实测生成 5000 行清单、2500 工件、25 类、50 来源组，配对失败 0，5000 个 SHA 全部重算。
- 原始 5000 JSON 不随包分发；无 raw 时验证级别只能是 `SOURCE_MANIFEST_AUDITED_NOT_RAW_VERIFIED`。
- 48 比较候选全部标 `semantic_alignment=UNVERIFIED`、`NOT_CERTIFIABLE_UNTIL_ALIGNED`，不生成虚假 LSTPN 故障证书。

## G1 R6-08 联合区间纠偏

- 修正审计发现的 Q 上界误拒：宽松上界 `[0,3/4]` 与 `[0,1/2]` 相交非空应收紧，只有下界 `3/5 > 1/2` 才矛盾。
- subject 与独立 oracle（线性可行性路径）20/20 一致，5/5 真实源码变异检出。
- 证据：`runs/g1_r608/results.csv`、`runs/g1_r608/summary.json`。

## 最终验收器防篡改

- `tests/final_verify_r6_e2.py` 从原始 CSV/文件重新计算计数与 SHA，不用硬编码通过统计。
- 负测：篡改一条 raw SHA → FAIL；删除一条 universe 行 → FAIL；翻转一个 G1 状态 → FAIL；未修改基线 → PASS。
- 证据：`runs/negative_controls/negative_controls.json`。

## 未闭合

- G0-1 实际生成、G0-2 语义对齐、G2—G5、经典基线、全量实验、敏感性矩阵、独立终验。
- 任何 P0 未解释，总体不得 `FULLY_CLOSED`。
