# R6-08 模块级错误路径检查（临时）

**`PASS_PROVISIONAL_R6_08_MODULE_NOT_PHASE_GATE`**

在 G1 区间纠偏之外，补齐 R6-08 作为模块的独立错误路径分类。subject/oracle 独立实现，10/10 用例一致。

## 覆盖错误路径

- `MODEL_INPUT_INVALID`：模型参数越界。
- `UNCERTIFIED_INTERVAL`：区间无认证来源。
- `COMPLEMENT_INFEASIBLE`：q0+q1=1 联合不可行。
- `BOUND_INVALID`：区间下界>上界或越出 [0,1]。
- `JOINT_INFEASIBLE`：Q 下界超过 q 上界。
- `SOURCE_INCONSISTENT`：同一事件质量源不一致。
- `CATEGORY_SUM_EXCEEDS`：观测类别质量和超过源质量。
- `NO_METHOD`：无有效积分方法。
- `SEARCH_INCOMPLETE`：候选搜索不完整，不能声称无歧义。
- `OK_DECIDED`：合法证据给出预期判定。

## 真实变异（3/3 检出）

1. `M_SKIP_COMPLEMENT_CHECK`：跳过 q0+q1=1 检查。
2. `M_ACCEPT_UNCERTIFIED`：接受无认证区间。
3. `M_DECIDE_WITHOUT_METHOD`：无积分方法仍判定。

## 证据

- `runs/g2_r608_module/results.csv`
- `runs/g2_r608_module/summary.json`
- `runs/g2_r608_module/mutations/*/mutation.patch`

不覆盖完整 13 边界 R6-08 套件或真实 SCG 轨迹上的所有错误路径；不关闭 G2。
