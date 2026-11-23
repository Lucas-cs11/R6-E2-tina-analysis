# R6-12 维护/再配置切换（临时）

**`PASS_PROVISIONAL_R6_12_PARTIAL_NOT_PHASE_GATE`**

两套独立实现（subject 区间边界分类、oracle 区间边界分类），5/5 用例一致。

## 覆盖场景

- 干净切换：切换时刻前后配置都存在，无跨越。
- 配置跨越切换时刻：返回非法证据。
- 切换前缺失配置：返回未决。
- 切换后缺失配置：返回未决。
- 端点切换：配置在切换时刻结束/开始，合法。

## 真实变异（3/3 检出）

1. `M_ALLOW_SPAN`：允许配置跨越切换时刻。
2. `M_REQUIRE_BOTH_SIDES`：放宽为必须两侧都缺失才未决（单侧缺失仍判定）。
3. `M_IGNORE_ENDPOINT`：端点不等号被改严格，端点切换被误判。

## 证据

- `runs/g2_r612/results.csv`
- `runs/g2_r612/summary.json`
- `runs/g2_r612/mutations/*/mutation.patch`

不覆盖一般再配置语义或完整 R6-12 套件；不关闭 G2。
