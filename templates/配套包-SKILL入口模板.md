# 配套包入口模板：{style-id}

> 对应 `references/paired-package-spec.md` 第一节与第二节。复制本模板为 `{style-id}/SKILL.md`，替换 `{...}` 占位；身份、版本、规则与特征配置写在 `references/style-contract.json`，本文件不复制规则表。

---
name: {style-id}
description: {一句话说明本包从什么材料、按什么写法、产出什么；在用户要求用该文风准备并转写、或继续本包任务时调用。}
---

# {display_name}（{style-id}）

## 定位

- 目标体裁与方向：{target_genre}
- 本包版本：{style_version} {status}
- 适用：{applicable_scenarios}
- 未验证：{unverified_scenarios}

## 一个入口，两项内部能力

| 阶段 | 读取 | 产出 |
|---|---|---|
| 准备 | `references/style-contract.json` + `references/preparation.md` | 已有立意直接沿用／简短方向待确认 → 自主选材 → 选材卡 |
| 转写 | `references/style-contract.json` + `references/rewriting.md` + 选材卡 + 完整原文与任务证据 | 正文 + 四项自查 |

不默认加载包外材料。准备判断需要某项转写细节时，按需补读 `rewriting.md`。

## 运行顺序

1. 判断任务方向（长转短／短转长／相近篇幅）；本包当前执行能力：{长转短等}。
2. 方向沟通保持轻量：用户已有明确立意直接沿用；只有材料时给出简短核心问题与预期判断，等待确认或修正。
3. 确认后自主选材与容量判断（按本套规则、目标篇幅与论证负担决定观点去留），留简短选材卡。
4. 按转写规则成稿；转写同时读取完整原文与任务证据，完成内容与条件、立意、文风特征、可读性四项检查。

## 确认条件

- 只有材料、没有立意时，简短方向需用户确认；已有明确立意或对等明确授权时直接继续，不重复索取确认。
- 用户否定方向时，按修正意见更新思路，不自行改立意。
- 观点取舍、段序与比例属自主选材范围，不要求用户逐项批准。
- 文件存在、模型自查通过都不能当作“用户已确认”或“用户满意”。

## 内部资源

- `references/style-contract.json`：唯一共享规范（身份、版本、边界、规则映射、特征配置）。
- `references/preparation.md`：本套准备规则。
- `references/rewriting.md`：本套转写规则。

## 边界

- 只使用本包文件、本次任务材料和适用的治理／基座规则；不读取原范文、旧稿、其他文风包或维护记录。
- 不复制原作者身份话术、样本全文或专属案例数值；证据编号只作来源标记。
- 公开边界与事实优先于文风还原；缺少必要条件时说明缺口，不虚构补齐。

## 检查

- 包结构：由提取器运行 `python scripts/package_check.py <本包目录>`；未实际运行不写“检查通过”。
- 证据：由 `evidence_check.py` 对实验证据表与分析文本回查。
