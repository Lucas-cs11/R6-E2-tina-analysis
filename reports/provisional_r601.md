# R6-01 区分子边界（端点/即时优先，临时）

**`PASS_PROVISIONAL_R6_01_PARTIAL_NOT_PHASE_GATE`**

两套独立实现：subject 用记录式互模拟（trace record），oracle 用区间点乘积枚举（signature）。两者在 3 例中关系完全一致。

## 覆盖子边界

- **端点等号**：`endpoint_grid=True` 时，非急流在区间端点的两个状态由不同的后续 delay 区分 → 可区分（undist=false）。
- **急流延迟**：`endpoint_grid=False` 时，急流 transition delay=0 与非急流 delay=1 产生相同 reachable 状态 → 不可区分（undist=true）。
- **急流优先**：急流在 delay=0 发射，先于 delay=1 的非急流 → 可区分（undist=false）。

## 真实变异（3/3 检出）

1. `M_DELAYED_BEFORE_URGENT`：急流被当作延迟处理，trace 记录改变。
2. `M_ENDPOINT_OPEN`：端点网格被忽略，端点等号不再区分。
3. `M_URGENT_NEVER_FIRES`：急流 transition 被移除，reachable 集改变。

## 证据

- `runs/g2_r601/results.csv`
- `runs/g2_r601/summary.json`
- `runs/g2_r601/mutations/*/mutation.patch`
- 失败批次 `failed_attempt1/`（Fraction JSON 序列化崩溃）

## 未覆盖

- 无界闭包、一般 timed automata、完整 R6-01 13 边界套件。不关闭 G2。
