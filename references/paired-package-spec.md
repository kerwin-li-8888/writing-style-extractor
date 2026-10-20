# 配套文风包规格（paired-package-spec）

> 适用版本：writing-style-extractor 0.3.0 正式。
> 本文规定配套文风包的目录、共享规范字段、准备与转写文件要求以及包检查判据，是 `templates/配套包-*` 四套模板与 `scripts/package_check.py` 的共同依据。字段名或允许值需要调整时，规格、模板、检查器三处同步，并在实验记录中说明理由。

## 一、一个入口，两项内部能力

配套文风包采用以下最小结构：

```text
{style-id}/
├── SKILL.md
└── references/
    ├── style-contract.json
    ├── preparation.md
    └── rewriting.md
```

- 对外只有一个调用入口 `SKILL.md`；产品意义上，`preparation.md` 是“准备 Skill”，`rewriting.md` 是“转写 Skill”。文件层面不拆成两个可被系统独立发现的技能，避免调用时错配。
- 两项能力共用同一个包版本，一起提取、调用、版本管理和验证；不单独发布准备或转写子版本。
- 准备阶段读取 `style-contract.json` 与 `preparation.md`；成稿阶段再读取 `rewriting.md`。准备判断需要某项转写细节时，按链接补读，不默认全量加载。
- 身份、版本、边界、规则与特征配置只在 `style-contract.json` 维护一次。`preparation.md` 与 `rewriting.md` 用规则编号引用，不复制另一份相同表格。
- 候选包先保存在实验目录（例如 `{实验目录}/packages/{style-id}/`），不安装到全局技能目录，不改正式档案。只有用户明示确认晋升后，才按正式位置部署并记录新状态。
- 只有 1 篇样本时生成的是**单篇候选包**：`sample_count` 为 1、`sample_ids` 为 `["S01"]`，`source_boundary` 必须写明“单篇、来源、是否核验、不能声称作者稳定风格或跨题材泛化”。单篇候选同样走候选状态，不因篇数少而降低证据与边界要求。
- 包内运行只依赖本包文件、本次任务材料和适用的治理／基座规则；不依赖包外的原范文、旧稿、维护记录或另一套文风包。

两套包可以共享工程规格、模板与通用方法底稿，但准备和转写文件必须按本套文风独立适配，不输出两个可以任意拼接的通用 Skill。规则映射按「范文特征 → 转写动作 → 所需材料 → 准备动作 → 成稿检查」建立；纯表达规则可以注明无需新增事实材料。

## 二、文件职责

| 文件 | 职责 | 何时读取 | 主要内容 |
|---|---|---|---|
| `SKILL.md` | 唯一入口 | 每次任务开始 | 名称与触发说明、核心目的、运行阶段、确认条件、内部文件路由、边界 |
| `references/style-contract.json` | 唯一共享规范 | 准备与转写都读 | 身份与边界、篇幅政策、规则映射、特征配置、内部资源 |
| `references/preparation.md` | 本套准备规则 | 准备阶段 | 方向识别、轻量方向沟通、材料盘点、确认闸门、自主选材与内容容量、选材卡格式 |
| `references/rewriting.md` | 本套转写规则 | 成稿阶段 | 结构推进、证据呈现、段落节奏、语言表达、四项检查、冲突处理 |

`SKILL.md` 应说明：准备阶段只做材料理解、思路提出与确认后的内容准备；确认前不得进入正式成稿。`rewriting.md` 不重新选择已确认立意。

## 三、style-contract.json 的结构

文件为 UTF-8 编码、可被 Python 标准库 `json` 直接解析的单个 JSON 对象。不引入数据库、服务或外部 schema 依赖。

### 3.1 顶层示例

以下 JSON 只演示字段结构，`S01-P05`、数值与场景文本均为占位，不代表任何真实样本或已生成包。

```json
{
  "schema_version": "1.0",
  "identity": {
    "style_id": "example-writing-style",
    "display_name": "示例文风",
    "style_version": "V0.4",
    "status": "候选",
    "target_genre": "中文长文转短文",
    "applicable_scenarios": [
      "把一篇信息密度较高的中文长文压缩为 600—900 字的可读短文",
      "材料包含可核对的案例、数字或其条件"
    ],
    "unverified_scenarios": [
      "短转长",
      "小说、诗歌、广告文案",
      "没有案例或数字支撑的纯观点材料"
    ],
    "sample_count": 1,
    "sample_ids": ["S01"],
    "source_boundary": "样本来自用户提供的公众号原文，未做第三方事实核验；结论只覆盖这些样本的可观察写法，不代表作者全部体裁或稳定风格。"
  },
  "length_policy": {
    "sample_observations": [
      {
        "sample_id": "S01",
        "body_chars_non_whitespace": 0,
        "paragraph_count": 0,
        "note": "示例占位；生成时填写实测值"
      }
    ],
    "target_adaptation": "先根据原文与输出要求判断长转短、短转长或相近篇幅，不能只按原文字数判断。观察值只用于理解范文体量，不自动成为新文章的最低字数或永久限制。"
  },
  "rules": [
    {
      "rule_id": "R01",
      "name": "用案例对照推进判断",
      "basis_type": "范文观察",
      "evidence_refs": ["S01-P05", "S01-P11-P14"],
      "basis_note": "",
      "feature_group": "核心",
      "default_enabled": true,
      "conditions": "材料中存在两个及以上可对照的案例或条件，且目标篇幅允许展开。",
      "rewriting_action": "先给对照条件，再呈现两侧结果，最后落到判断；不把单侧结果写成普遍结论。",
      "required_materials": [
        "案例双方的名称或可公开指代",
        "对照条件",
        "两侧结果及来源"
      ],
      "preparation_action": "准备阶段核对案例与对照条件是否成组存在；缺少任一侧时标记缺口，不补造案例。",
      "final_check": "成稿检查案例两侧条件是否同时出现，判断是否越过材料支持范围。"
    },
    {
      "rule_id": "R02",
      "name": "段落收束先给结论再解释",
      "basis_type": "通用执行方法",
      "evidence_refs": [],
      "basis_note": "通用可读性方法，不是从样本观察到的作者特征。",
      "feature_group": "可选",
      "default_enabled": false,
      "conditions": "段落较长且读者需要快速抓住判断时。",
      "rewriting_action": "段首给一句结论，再展开原因；避免每段都以背景铺陈开头。",
      "required_materials": [],
      "preparation_action": "无需新增事实材料；准备阶段只在内容包中标记该段的核心判断。",
      "final_check": "抽查段首是否能独立说明本段判断。"
    }
  ],
  "feature_config": {
    "group_values": ["核心", "条件", "可选"],
    "default_toggle_field": "default_enabled",
    "manual_selection": "用户可用自然语言点名要启用或排除的特征，如“这次不要案例对照”；模型把选择映射为规则编号并记录在本次任务记录中。未点名时按每条规则的 default_enabled 执行，不默认全开。"
  },
  "resources": {
    "preparation": "references/preparation.md",
    "rewriting": "references/rewriting.md",
    "external_dependencies": []
  }
}
```

### 3.2 字段约定

顶层字段：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `schema_version` | string | 是 | 当前为 `"1.0"`；结构不兼容变更时递增 |
| `identity` | object | 是 | 见下表 |
| `length_policy` | object | 是 | 见下表 |
| `rules` | array | 是 | 至少一条；见下表 |
| `feature_config` | object | 是 | 见下表 |
| `resources` | object | 是 | 见下表 |

`identity`：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `style_id` | string | 是 | 小写字母、数字、连字符；与包目录名、`SKILL.md` frontmatter 的 `name` 一致 |
| `display_name` | string | 是 | 面向用户的文风名称 |
| `style_version` | string | 是 | 如 `"V0.4"`；显示时与 `status` 组合为“V0.4 候选” |
| `status` | string | 是 | `候选` / `已验证` / `停用`。生成候选包时只能写 `候选`；晋升为 `已验证` 需用户明示确认 |
| `target_genre` | string | 是 | 目标体裁与转写方向，如“中文长文转短文” |
| `applicable_scenarios` | array[string] | 是 | 至少一项；写本次有证据支持的使用场景 |
| `unverified_scenarios` | array[string] | 是 | 至少一项；写明确未验证或本版不支持的方向 |
| `sample_count` | integer | 是 | 独立样本数，≥1；1 表示单篇候选。重复文章与同一文章的改写版本不重复计数 |
| `sample_ids` | array[string] | 是 | 与 `sample_count` 等长、唯一，使用 `S{nn}` |
| `source_boundary` | string | 是 | 样本来源与可信边界：谁提供、是否核验、能声称什么、不能声称什么；单篇时必须写明只覆盖该篇、不声称作者稳定风格或跨题材泛化 |

`length_policy`：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `sample_observations` | array[object] | 是 | 每项含 `sample_id`（string）、`body_chars_non_whitespace`（integer，≥0）、`paragraph_count`（integer，≥0）、`note`（string）；数值是观察值 |
| `target_adaptation` | string | 是 | 写目标篇幅如何适配；必须说明观察值不自动成为最低字数、永久上限或所有任务的固定值 |

`rules` 的每一项：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `rule_id` | string | 是 | 形如 `R01`（`^R\d{2}$`）；同一文件内唯一 |
| `name` | string | 是 | 规则名称 |
| `basis_type` | string | 是 | `范文观察` / `通用执行方法` / `用户反馈适配` 三值之一 |
| `evidence_refs` | array[string] | 是 | `范文观察` 至少一条真实引用；其余两类必须为空数组 |
| `basis_note` | string | 是 | `范文观察` 可留空；`通用执行方法` 与 `用户反馈适配` 必须写明来源性质，且不得含 `S{nn}-P{nn}` 形式的样本引用 |
| `feature_group` | string | 是 | 取 `feature_config.group_values` 之一 |
| `default_enabled` | boolean | 是 | 未指定时是否启用；可选动作通常为 `false` |
| `conditions` | string | 是 | 适用条件；条件规则必须写清触发情境 |
| `rewriting_action` | string | 是 | 可执行的转写动作，不写抽象口号 |
| `required_materials` | array[string] | 是 | 所需材料；纯表达规则可为空数组，但 `preparation_action` 要说明无需新增材料及核对什么 |
| `preparation_action` | string | 是 | 准备阶段做什么；材料非空时写清寻找办法与缺少时的处理，不补造 |
| `final_check` | string | 是 | 成稿时检查什么，可逐条核对 |

`feature_config`：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `group_values` | array[string] | 是 | 必须恰好包含 `核心`、`条件`、`可选` 三项 |
| `default_toggle_field` | string | 是 | 固定为 `"default_enabled"`，指向每条规则的默认启停字段 |
| `manual_selection` | string | 是 | 用户如何用自然语言点名启用／排除特征，模型如何映射为规则编号并记录 |

每条规则的 `feature_group` 与 `default_enabled` 是实际归属与默认启停；`feature_config` 只定义允许值、默认字段名与用户选择方式，不重复维护规则名单。

`resources`：

| 字段 | 类型 | 必填 | 约定 |
|---|---|---|---|
| `preparation` | string | 是 | 包内相对路径，固定为 `references/preparation.md`，文件必须存在 |
| `rewriting` | string | 是 | 包内相对路径，固定为 `references/rewriting.md`，文件必须存在 |
| `external_dependencies` | array | 是 | 必须为空数组；任何包外执行依赖都无效 |

字段名不得自行改名。需要新增字段时，先改本规格，再同步模板与检查器，不先改包内 JSON。

### 3.3 依据类型三值约定

| 依据类型 | 含义 | `evidence_refs` | `basis_note` | 可以声称 | 不得包装成 |
|---|---|---|---|---|---|
| `范文观察` | 从本次选定样本的可观察写法提炼 | 至少一条真实 `S{nn}-P{nn}` 引用 | 可空；可写观察口径与反例 | “来自本组样本的观察” | 全部作者、全部体裁的稳定特征 |
| `通用执行方法` | 可读性、结构、表达等通用写作方法 | 空数组 | 必填，写明“通用方法，非样本观察”及依据性质 | “通用执行方法” | 作者特征、样本证据 |
| `用户反馈适配` | 本次用户明确提出的偏好或修正 | 空数组 | 必填，写明反馈时间与内容性质 | “按用户反馈适配” | 样本观察、作者稳定特征 |

- 只有 `范文观察` 可以声称来自样本。找不到真实定位的观察，降级为 `通用执行方法`，或标“证据不足”而不写成规则；不得编造引用。
- `S{nn}-P{nn}` 只作来源标记，不构成运行依赖。运行时不要求打开原范文或证据表；证据回查由 `evidence_check.py` 在实验档案中完成。
- 同一规则若同时有样本观察与通用方法成分，拆成两条，或把主依据写成 `范文观察` 并在 `basis_note` 说明通用成分；不得把通用方法混入 `evidence_refs`。

### 3.4 证据引用格式

- 单段：`S01-P05`。
- 区间：`S01-P55-P61`。
- 结构跨度：`S01-P02→P21`。
- 引用必须能在对应分析文本的 `【Pnn】` 行回查到；查不到即删除或降级，不用模型印象补位。
- 检查器使用的格式约束：`^S\d{2}-P\d{2}(?:-P\d{2}|→P\d{2})?$`。
- 旧证据使用 `note.md` 行号时，必须先建立原行号到分析段落内容的真实对应，再写 `S{nn}-P{nn}`；不得机械查找替换。

## 四、preparation.md 的内容要求

每套包独立撰写，依据本套共享规范适配，不复制另一套准备文件只改名称。至少包含：

1. **角色与边界**：本文件只负责本套文风的准备；身份、版本、规则以 `style-contract.json` 为准；不依赖包外通用准备 Skill、原范文、旧稿或维护记录。
2. **输入**：待转写材料、输出目标（篇幅、形式、读者）、已有立意与必保内容、用户已选特征。用户没有提供的信息由模型从材料理解后主动提出，不要求用户先拆全文、写提纲或填完整事实表。
3. **方向识别**：结合原文与输出目标判断长转短、短转长或相近篇幅，不能只按原文字数判断。写清本包当前执行能力（本轮为长转短）；其他方向如实说明边界与缺口，不直接套用长转短规则成稿。
4. **材料盘点**：按共享规范中本次适用的规则编号逐条核对 `required_materials`，标记“现有／缺失／待核”。数字与必要条件成组；作者经历属于素材作者，不写成用户亲历；公开边界单独列出。
5. **方向沟通（确认前）**：用户已有明确立意时直接沿用，不重复索取同一确认；只有材料时，主动给出简短的核心问题与预期判断（一至几段话），说明拟传达判断、用什么证据推进、主要保留与舍弃、影响方向的材料缺口。不设硬性字数，不要求用户填写完整大纲或批准逐段提纲。
6. **确认闸门**：方向经用户确认或修正后才进入正式选材与成稿；未回复时保持待确认，不把沉默或经过一段时间当成批准。已有对等明确授权（如“按这个方向直接写”）时，记录依据后继续，不重复设置大纲审批。用户只确认核心方向时，段序、比例、观点取舍与规则编号不要求逐项批准。
7. **确认后的自主选材与关系拆解**：方向确认后自行完成内容容量判断与选材——结合本套文风、目标篇幅、论证负担和必要条件决定保留多少观点，相近观点合并，独立支线舍弃——再按观点、事实、证据、前提、推导、结果、来源拆解；数字与必要条件成组，不摘掉条件单独填入文风结构。需要核验的事项标注状态；缺少核心材料时写明缺口，不虚构、不偷偷更换立意。
8. **选材卡（交给转写）**：轻量 Markdown，几句话或短列表，至少包含：核心判断、入选观点及关系、主要支持材料（含条件与来源）、舍弃项、必要条件与公开边界、未解决事项。不要求每篇填满表格；完整原文与任务证据同时整体传给转写，选材卡不是唯一材料。选材卡是执行者内部交付，不增加用户填表工作，也不预写成一篇通用稿后只替换措辞。
9. **禁止事项**：确认前不进入正式成稿；不重新选择已确认立意；准备只约束内容去留，不预写开场、逐段功能、句式或半成稿；不补造事实、数据、经历或案例数值；不把原作者身份话术、样本全文或专属案例数值带入包内；不向用户展示内部状态名、JSON 字段或检查器细节。

## 五、rewriting.md 的内容要求

每套包独立撰写，使用同一份共享规范。至少包含：

1. **角色与边界**：接收准备阶段的内容包，按本套规则组织表达并完成正文与检查；不重新选择或改变已确认立意；不依赖包外旧稿、原范文、维护记录或另一套文风包。
2. **输入**：选材卡、完整原文与任务证据、已确认方向、`style-contract.json`、本次特征配置、目标篇幅与形式。选材卡约束内容去留，不是唯一材料；需要原文条件、上下文或核验状态时回到完整原文取用。材料不足或条件缺失时回到准备或用户，不自行补齐。
3. **组织与表达**：按规则编号安排开场、推进、案例与证据呈现、段落节奏、句式语气与收束；内容去留依据选材卡，事实与条件从完整原文取用，不把事实检查过程写进正文。核心规则默认执行；条件规则只在条件成立时启用；可选规则按 `default_enabled` 与用户选择执行，不默认全开。
4. **四项检查**：
   - **内容与条件**：事实、数字、必要条件和来源是否保留并成组；有无虚构、经历挪用或条件缺失。
   - **立意**：是否遵循已确认的核心问题与判断；有无在成稿阶段改换方向。
   - **文风特征**：样本观察规则是否落实；通用方法与用户反馈是否被误当作者特征；是否抄用样本独特句、身份话术或专属数值。
   - **可读性**：是否能自然读完；有无规则堆叠、重复、衔接生硬或为凑特征牺牲表达。
5. **冲突处理**：事实、公开边界与已确认立意是硬约束；其次落实任务明确要求；文风规则在上述范围内发挥作用。目标篇幅与必要条件冲突、或缺少核心材料时，在准备报告或成稿报告中提出可行调整，由用户选择，不擅自删条件或补故事。冲突处理结果按四态登记在运行记录：默认规则直接满足／补充材料后满足／用户确认调整后的改编／仍不适配；用户未授权时不自动降低核心要求，改变规则后的结果不称为原规则通过。
6. **输出与记录**：交付正文与四项自查说明；自查通过不登记为“用户满意”。每篇的立意、准备结果与正文只留在本次运行记录，不写回包；确有跨任务适用的规则修改时另记包版本。
7. **禁止事项**：不重新选择已确认立意；不新增事实、数据或经历；不复制样本全文、原作者身份元素或特定案例专属数值；不把全部可选特征默认打开；不以文风规则为由越过公开边界。

## 六、包内禁止事项与运行边界

- 不携带真实范文全文或大段可替代原文的摘录；不携带原作者自称、栏目标签、互动话术、标志性收尾等身份元素。
- 不携带特定案例的专属数值、财务口径或复算结论；案例只能作为适用示例，不要求每篇文章都具备同类要素。
- 证据编号只作来源标记。包内不得要求运行时读取原范文、证据表、旧稿、维护记录、工程方案或另一套文风包；`resources.external_dependencies` 必须为空。
- 包内不保存用户确认、试写结果或评估结论。文件存在不能推断为用户确认或试写通过；这些状态记录在实验运行记录与档案协议中。
- 包内不预设本次任务未确认的立意、事实、经历或推荐结论。素材作者的经历不得归给用户。
- 准备与转写文件使用包内相对引用；不得出现绝对路径、`..` 跳转或指向包外的执行依赖。
- 公开边界与事实优先级高于文风还原度。缺少必要条件时说明缺口，不用虚构或偷偷更换立意填满结构。
- 证据强度按类型如实处理：记忆、举例、事实、判断不互相冒充；条件中的“或”“可能”等语义不得压掉；脱敏只移除属性，不引入新属性。

## 七、package_check.py 验收判据

命令接口：

```text
python scripts/package_check.py <文风包目录>
```

有效包返回 `0`；无效包返回非零，并逐条输出具体文件、字段路径或 JSON 位置。检查器只做结构与字段约定检查，不判断文风效果、内容真实性或用户满意度。

检查项：

| # | 判据 | 失败示例与定位 |
|---|---|---|
| 1 | 必要组件存在：目录、`SKILL.md`、`references/style-contract.json`、`references/preparation.md`、`references/rewriting.md` | 缺少准备组件：报告 `references/preparation.md: missing`，返回非零 |
| 2 | `SKILL.md` 有可解析的 frontmatter，含非空 `name` 与 `description` | 缺 `description`：报告 `SKILL.md: frontmatter.description missing` |
| 3 | `style-contract.json` 可被标准库 `json` 解析，顶层键齐全，`schema_version` 为 `"1.0"` | JSON 语法错误：报告行列位置；缺顶层键：报告 `style-contract.json: identity missing` |
| 4 | 身份与版本明确：`style_id`、`display_name`、`style_version`、`status` 非空；`style_id` 与目录名、`SKILL.md` 的 `name` 一致；`status` 在允许值内 | 不一致：报告 `identity.style_id` 与入口 `name` 的实际值 |
| 5 | 规则编号唯一：每条 `rule_id` 匹配 `R` 加两位数字，文件内无重复 | 重复：报告 `rules[3].rule_id: R02 duplicated (also rules[1])` |
| 6 | 每条规则映射完整：`rule_id`、`name`、`basis_type`、`evidence_refs`、`basis_note`、`feature_group`、`default_enabled`、`conditions`、`rewriting_action`、`required_materials`、`preparation_action`、`final_check` 均存在且类型正确；`feature_group` 在 `group_values` 内；`default_enabled` 为布尔值；`required_materials` 非空时 `preparation_action` 不得为空 | 缺 `preparation_action`：报告 `rules[0].preparation_action: missing`；材料非空但准备动作为空：报告 `rules[0].preparation_action: empty for required_materials`；可选动作全默认开启时报告具体规则编号 |
| 7 | 组件引用包内有效：`resources.preparation` 与 `resources.rewriting` 为包内相对路径且文件存在；`external_dependencies` 为空；资源路径不含绝对路径或 `..` | 指向包外：报告 `resources.external_dependencies: non-empty` 或具体路径 |
| 8 | 范文观察规则必须有证据引用：`basis_type == 范文观察` 时 `evidence_refs` 非空，且每条匹配 `S{nn}-P{nn}`、区间或跨度格式 | 缺失：报告 `rules[2].evidence_refs: empty for 范文观察`；格式错误：报告具体引用 |
| 9 | 通用方法不得伪称范文证据：`通用执行方法` 与 `用户反馈适配` 的 `evidence_refs` 必须为空，`basis_note` 非空且不含 `S{nn}-P{nn}` | 伪称：报告 `rules[4].evidence_refs: must be empty for 通用执行方法` |
| 10 | 样本字段一致：`sample_count` 与 `sample_ids` 数量一致、编号唯一；`length_policy.sample_observations` 非空，且其中的 `sample_id` 均属于 `sample_ids` | 不一致：报告两侧实际数量；未知样本：报告 `length_policy.sample_observations[0].sample_id: S99 not in sample_ids` |

补充约定：

- 检查器不校验证据是否真实；真实定位由 `evidence_check.py` 在实验档案中回查。
- 检查器不校验正文文风、内容忠实或公开边界；这些由真实试写后的人工评估完成。
- 不以“只匹配标题”或“只检查文件存在”的测试证明可用。反例至少覆盖：缺少准备组件、核心规则缺配套材料处理、执行依赖指向包外、`范文观察` 缺证据、通用方法带样本引用。
- 未实际运行检查器时，实施记录不得写“包结构检查已通过”；本规格本身不构成检查结果。
