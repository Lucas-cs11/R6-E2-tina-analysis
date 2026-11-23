# R6-E2 剩余阻断

## 已修复的 R6-E1 审计 P0

1. `R6-08-QY-CONSISTENCY`：Q 上界相交而非误拒，已修正并 20/20、5/5 变异通过。
2. `FINAL-VERIFY-TAMPER`：终验重新计算计数/SHA，篡改负测 3/3 拒绝、基线通过。
3. `RAW-PORTABILITY`：`--raw-root` 参数化，来源清单可重放；5000 原始 JSON 仍不入包，等级 `SOURCE_MANIFEST_AUDITED`。

## 仍未闭合

1. `GENERATOR-SCOPE-143360`：候选已全枚举，107,520 合法格已实际生成并结构验证通过；但尚未执行四实现诊断，54 与 143360 的研究域裁定未由主理论助手完成。
2. `FRESH-LOGIC-ENGINE`：新独立四实现诊断引擎未构建。
3. `FULL-PYS-PIPELINE`：48 候选语义已核实为不可认证（仅经验分类）；5000 全量建模、32 工况新认证未执行。
4. `G2-PARTIAL`：R6-01—R6-13 全部有临时组件（13 组件 36 变异），但完整套件与正式阶段 PASS 未声明；其余 R6-01 端点/即时优先、R6-07/11 已临时组件通过；正式 G2 阶段 PASS 未声明。
5. `BASELINES-SENSITIVITY`：逻辑 1620 已生成；历史 52 模型同题适配器已验证 36 个；18 项外部基线仍 NOT_AVAILABLE；概率 567/判定 135 仍 PENDING_SPEC。
6. `BASELINES-SENSITIVITY` 已登记 18 项，但全部 `NOT_AVAILABLE`/`UNASSESSED`。
7. `INDEPENDENT-SIGNOFF`：G5 独立终验未执行。

## 阶段

- G0：`PARTIAL`
- G1：`PARTIAL_VALIDATED`
- G2：`PARTIAL`
- G4/G5：`NOT_EXECUTED`
- G7：`NOT_CLOSED`
- 总体：`PARTIAL_VALIDATED_NOT_CLOSED`
