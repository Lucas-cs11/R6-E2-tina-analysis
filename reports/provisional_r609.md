# R6-09 离散支持序列似然/后验（临时）

**`PASS_PROVISIONAL_R6_09_PARTIAL_NOT_PHASE_GATE`**

两套独立实现：subject 精确有理前向乘积；oracle 对数域求和。5/5 用例类别一致，后验值在 1e-9 容差内一致。

## 覆盖场景

- `LIKE_POSTERIOR`：等长序列，后验偏向发射概率匹配的假设。
- `ZERO_LIKELIHOOD`：序列在两个假设下似然均为 0，返回未决。
- `EVIDENCE_BELOW_BOUND`：证据下界低于认证阈值，返回未决。
- `NORMALIZATION_MISMATCH`：先验不归一，返回非法证据。
- `BIASED_POSTERIOR`： biased 序列产生极端后验。

## 真实变异（3/3 检出）

1. `M_SKIP_ZERO_CHECK`：跳过零似然检查（导致除零异常，检出）。
2. `M_ACCEPT_BAD_PRIOR`：接受不归一先验。
3. `M_IGNORE_EVIDENCE_BOUND`：忽略证据下界。

## 证据

- `runs/g2_r609/results.csv`
- `runs/g2_r609/summary.json`
- `runs/g2_r609/mutations/*/mutation.patch`

不覆盖连续发射分布或完整 R6-09 套件；不关闭 G2。
