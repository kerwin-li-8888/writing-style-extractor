#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""package_check.py —— 配套文风包结构检查

用法：
    python package_check.py <文风包目录>

依据 references/paired-package-spec.md 第七节的 10 条判据检查一个配套文风包：
  1. 必要组件：SKILL.md、references/style-contract.json、
     references/preparation.md、references/rewriting.md。
  2. SKILL.md 有可解析的 frontmatter，name 与 description 非空。
  3. style-contract.json 可被标准库 json 解析；顶层键齐全；
     schema_version 为 "1.0"。
  4. 身份与版本：style_id/display_name/style_version/status 非空；
     style_id 与目录名、SKILL.md name 一致；status 在允许值内。
  5. rule_id 唯一，格式为 ^R\d{2}$。
  6. 每条规则 12 个字段齐全、类型正确；feature_group 在
     feature_config.group_values 内；default_enabled 为布尔；
     required_materials 非空时 preparation_action 不得为空。
  7. resources.preparation/rewriting 为包内相对路径且文件存在；
     external_dependencies 为空数组。
  8. 范文观察规则 evidence_refs 非空且格式合法。
  9. 通用执行方法/用户反馈适配 evidence_refs 为空，basis_note 非空
     且不含 S{nn}-P{nn} 引用。
  10. sample_count 与 sample_ids 等长且唯一；sample_observations 非空，
      其 sample_id 均属于 sample_ids，数值字段为整数。

另按规格第三节检查 identity 其余必填字段、feature_config 固定值和样本编号
格式；可选规则全部默认启用时输出提示（不判失败）。
检查器只做结构与字段约定检查，不判断文风效果、内容真实性或用户满意度。
证据是否真实可回查由 evidence_check.py 在实验档案中完成。

退出码：
    0 = 结构与字段约定全部通过
    1 = 发现结构或字段约定问题（逐条给出文件、字段路径与描述）
    2 = 输入错误（参数数量不对、目录不存在或不是目录）

示例：
    python package_check.py path/to/{style-id}
"""
import json
import os
import re
import sys
from collections import Counter

SKILL_LABEL = 'SKILL.md'
CONTRACT_LABEL = 'references/style-contract.json'
PREP_LABEL = 'references/preparation.md'
REWRITE_LABEL = 'references/rewriting.md'

TOP_KEYS = ['schema_version', 'identity', 'length_policy', 'rules',
            'feature_config', 'resources']
IDENTITY_TEXT_KEYS = ['style_id', 'display_name', 'style_version', 'status',
                      'target_genre', 'source_boundary']
SCENARIO_KEYS = ['applicable_scenarios', 'unverified_scenarios']
STATUS_VALUES = ['候选', '已验证', '停用']
BASIS_TYPES = ['范文观察', '通用执行方法', '用户反馈适配']
GROUP_VALUES = ['核心', '条件', '可选']
RULE_FIELDS = ['name', 'basis_type', 'evidence_refs', 'basis_note',
               'feature_group', 'default_enabled', 'conditions',
               'rewriting_action', 'required_materials',
               'preparation_action', 'final_check']
RULE_TYPES = {
    'name': 'str',
    'basis_type': 'str',
    'evidence_refs': 'list',
    'basis_note': 'str',
    'feature_group': 'str',
    'default_enabled': 'bool',
    'conditions': 'str',
    'rewriting_action': 'str',
    'required_materials': 'list',
    'preparation_action': 'str',
    'final_check': 'str',
}

RULE_ID_RE = re.compile(r'^R\d{2}$')
STYLE_ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SAMPLE_ID_RE = re.compile(r'^S\d{2}$')
EVIDENCE_RE = re.compile(r'^S\d{2}-P\d{2}(?:-P\d{2}|→P\d{2})?$')
SAMPLE_CITE_RE = re.compile(r'S\d{2}-P(?:\d{2})?')
DRIVE_RE = re.compile(r'^[A-Za-z]:')

TYPE_NAMES = {
    'dict': '对象',
    'list': '数组',
    'str': '字符串',
    'bool': '布尔值',
    'int': '整数',
    'float': '数值',
    'NoneType': 'null',
}


def type_name(value):
    return TYPE_NAMES.get(type(value).__name__, type(value).__name__)


def is_text(value):
    return isinstance(value, str) and value.strip() != ''


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def fmt(value, limit=80):
    """把实际值压成一行，便于诊断定位。"""
    try:
        text = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) > limit:
        text = text[:limit] + '…'
    return text


class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, label, path, message):
        if path:
            self.errors.append('%s: %s: %s' % (label, path, message))
        else:
            self.errors.append('%s: %s' % (label, message))

    def warn(self, message):
        self.warnings.append(message)


def read_text(path, label, report):
    """读取 UTF-8 文本；失败时登记问题并返回 None。"""
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as exc:
        report.error(label, '', '无法读取（需 UTF-8）：%s' % exc)
        return None


def check_components(pkg_dir, report):
    """判据 1：必要组件存在。返回各组件实际路径。"""
    paths = {
        SKILL_LABEL: os.path.join(pkg_dir, 'SKILL.md'),
        CONTRACT_LABEL: os.path.join(pkg_dir, 'references',
                                     'style-contract.json'),
        PREP_LABEL: os.path.join(pkg_dir, 'references', 'preparation.md'),
        REWRITE_LABEL: os.path.join(pkg_dir, 'references', 'rewriting.md'),
    }
    for label, path in paths.items():
        if not os.path.isfile(path):
            report.error(label, '', 'missing')
    return paths


def unquote(value):
    """去掉包裹 name/description 的成对引号。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace('\\n', ' ')
        else:
            inner = inner.replace("''", "'")
        return inner
    return value


def parse_frontmatter(lines, report):
    """手写最小 YAML 头解析：只取顶层 key: value，支持 |/> 块。

    不引入第三方 YAML 库；只关心 frontmatter 中的标量字段，嵌套结构忽略。
    """
    if not lines or lines[0].strip() != '---':
        report.error(SKILL_LABEL, 'frontmatter',
                     'missing（文件第一行必须是 ---）')
        return None
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == '---':
            end = idx
            break
    if end is None:
        report.error(SKILL_LABEL, 'frontmatter',
                     'missing（缺少结束的 ---）')
        return None

    data = {}
    idx = 1
    while idx < end:
        line = lines[idx]
        if not line.strip() or line.lstrip().startswith('#'):
            idx += 1
            continue
        if line[:1].isspace():
            idx += 1  # 嵌套行不参与最小解析
            continue
        match = re.match(r'^([A-Za-z0-9_-]+)\s*:\s*(.*)$', line)
        if not match:
            idx += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in ('|', '>', '|-', '>-', '|+', '>+'):
            folded = value.startswith('>')
            block = []
            idx += 1
            while idx < end:
                nxt = lines[idx]
                if nxt.strip() and not nxt[:1].isspace():
                    break
                block.append(nxt.strip())
                idx += 1
            while block and not block[-1]:
                block.pop()
            data[key] = (' ' if folded else '\n').join(block).strip()
            continue
        data[key] = unquote(value)
        idx += 1
    return data


def check_skill_md(path, report):
    """判据 2：frontmatter 可解析，name/description 非空。返回 name。"""
    text = read_text(path, SKILL_LABEL, report)
    if text is None:
        return None
    front = parse_frontmatter(text.splitlines(), report)
    if front is None:
        return None

    entry_name = None
    for key in ('name', 'description'):
        if key not in front:
            report.error(SKILL_LABEL, 'frontmatter.%s' % key, 'missing')
        elif not is_text(front[key]):
            report.error(SKILL_LABEL, 'frontmatter.%s' % key,
                         'empty（必须是非空字符串）')
    if is_text(front.get('name')):
        entry_name = front['name'].strip()
    return entry_name


def load_contract(path, report):
    """判据 3：标准库 json 解析。返回 (是否读到 JSON, 对象)。"""
    text = read_text(path, CONTRACT_LABEL, report)
    if text is None:
        return False, None
    try:
        return True, json.loads(text)
    except json.JSONDecodeError as exc:
        report.error(CONTRACT_LABEL, '',
                     'JSON 语法错误（第 %d 行第 %d 列）：%s'
                     % (exc.lineno, exc.colno, exc.msg))
        return False, None


def check_identity(identity, dir_name, entry_name, report):
    """判据 4 及规格 3.2 的 identity 必填字段。"""
    if not isinstance(identity, dict):
        report.error(CONTRACT_LABEL, 'identity',
                     '必须是 JSON 对象（实际为%s）' % type_name(identity))
        return

    for key in IDENTITY_TEXT_KEYS:
        path = 'identity.%s' % key
        if key not in identity:
            report.error(CONTRACT_LABEL, path, 'missing')
        elif not is_text(identity[key]):
            report.error(CONTRACT_LABEL, path,
                         'empty（必须是非空字符串）')

    style_id = identity.get('style_id')
    if is_text(style_id):
        style_id = style_id.strip()
        if not STYLE_ID_RE.match(style_id):
            report.error(CONTRACT_LABEL, 'identity.style_id',
                         '格式不符：%s（只允许小写字母、数字与连字符，'
                         '连字符不得位于开头、结尾或连续出现）' % fmt(style_id))
        if style_id != dir_name:
            report.error(CONTRACT_LABEL, 'identity.style_id',
                         '与包目录名不一致：%s ≠ %s'
                         % (fmt(style_id), fmt(dir_name)))
        if entry_name is not None and style_id != entry_name:
            report.error(CONTRACT_LABEL, 'identity.style_id',
                         '与 SKILL.md frontmatter.name 不一致：%s ≠ %s'
                         % (fmt(style_id), fmt(entry_name)))

    status = identity.get('status')
    if is_text(status) and status.strip() not in STATUS_VALUES:
        report.error(CONTRACT_LABEL, 'identity.status',
                     '不在允许值内：%s（允许 %s）'
                     % (fmt(status), '、'.join(STATUS_VALUES)))

    for key in SCENARIO_KEYS:
        check_scenario_list(identity, key, report)


def check_scenario_list(identity, key, report):
    """附带检查：适用与未验证场景至少一项。"""
    path = 'identity.%s' % key
    if key not in identity:
        report.error(CONTRACT_LABEL, path, 'missing')
        return
    value = identity[key]
    if not isinstance(value, list):
        report.error(CONTRACT_LABEL, path,
                     '必须是数组（实际为%s）' % type_name(value))
        return
    if not value:
        report.error(CONTRACT_LABEL, path, '至少需要一项')
        return
    for idx, item in enumerate(value):
        if not is_text(item):
            report.error(CONTRACT_LABEL, '%s[%d]' % (path, idx),
                         '必须是非空字符串')


def check_feature_config(feature_config, report):
    """判据 6 的 group_values 来源及规格 3.2 的固定字段。

    返回 group_values（无效时为 None）。
    """
    if not isinstance(feature_config, dict):
        report.error(CONTRACT_LABEL, 'feature_config',
                     '必须是 JSON 对象（实际为%s）' % type_name(feature_config))
        return None

    group_values = None
    path = 'feature_config.group_values'
    if 'group_values' not in feature_config:
        report.error(CONTRACT_LABEL, path, 'missing')
    elif not isinstance(feature_config['group_values'], list):
        report.error(CONTRACT_LABEL, path,
                     '必须是数组（实际为%s）'
                     % type_name(feature_config['group_values']))
    else:
        group_values = feature_config['group_values']
        strings = []
        for idx, item in enumerate(group_values):
            if not isinstance(item, str):
                report.error(CONTRACT_LABEL, '%s[%d]' % (path, idx),
                             '必须是字符串（实际为%s）' % type_name(item))
            else:
                strings.append(item)
        missing = [v for v in GROUP_VALUES if v not in strings]
        extra = [v for v in strings if v not in GROUP_VALUES]
        duplicated = [v for v, n in Counter(strings).items() if n > 1]
        if missing:
            report.error(CONTRACT_LABEL, path,
                         '缺少必需值：%s' % '、'.join(missing))
        if extra:
            report.error(CONTRACT_LABEL, path,
                         '含未定义值：%s' % '、'.join(extra))
        if duplicated:
            report.error(CONTRACT_LABEL, path,
                         '含重复值：%s' % '、'.join(duplicated))

    if 'default_toggle_field' not in feature_config:
        report.error(CONTRACT_LABEL, 'feature_config.default_toggle_field',
                     'missing')
    elif feature_config['default_toggle_field'] != 'default_enabled':
        report.error(CONTRACT_LABEL, 'feature_config.default_toggle_field',
                     '必须固定为 "default_enabled"（实际为%s）'
                     % fmt(feature_config['default_toggle_field']))

    if 'manual_selection' not in feature_config:
        report.error(CONTRACT_LABEL, 'feature_config.manual_selection',
                     'missing')
    elif not is_text(feature_config['manual_selection']):
        report.error(CONTRACT_LABEL, 'feature_config.manual_selection',
                     'empty（必须是非空字符串）')

    return group_values


def check_rule_id(rule, idx, seen, report):
    """判据 5：rule_id 格式与唯一性。返回 rule_id 或 None。"""
    base = 'rules[%d]' % idx
    path = base + '.rule_id'
    if 'rule_id' not in rule:
        report.error(CONTRACT_LABEL, path, 'missing')
        return None
    rule_id = rule['rule_id']
    if not isinstance(rule_id, str):
        report.error(CONTRACT_LABEL, path,
                     '必须是字符串（实际为%s）' % type_name(rule_id))
        return None
    if not RULE_ID_RE.match(rule_id):
        report.error(CONTRACT_LABEL, path,
                     '格式不符：%s（应为 R 加两位数字，如 R01）'
                     % fmt(rule_id))
    if rule_id in seen:
        report.error(CONTRACT_LABEL, path,
                     '%s 重复（另见 rules[%d]）' % (fmt(rule_id), seen[rule_id]))
    else:
        seen[rule_id] = idx
    return rule_id


def check_rule_fields(rule, idx, report):
    """判据 6 前半：12 字段存在且类型正确（rule_id 另行检查）。"""
    base = 'rules[%d]' % idx
    for field in RULE_FIELDS:
        path = '%s.%s' % (base, field)
        if field not in rule:
            report.error(CONTRACT_LABEL, path, 'missing')
            continue
        value = rule[field]
        kind = RULE_TYPES[field]
        if kind == 'str':
            if not isinstance(value, str):
                report.error(CONTRACT_LABEL, path,
                             '必须是字符串（实际为%s）' % type_name(value))
        elif kind == 'bool':
            if not isinstance(value, bool):
                report.error(CONTRACT_LABEL, path,
                             '必须是布尔值（实际为%s）' % type_name(value))
        elif kind == 'list':
            if not isinstance(value, list):
                report.error(CONTRACT_LABEL, path,
                             '必须是数组（实际为%s）' % type_name(value))
                continue
            for item_idx, item in enumerate(value):
                if not isinstance(item, str):
                    report.error(CONTRACT_LABEL,
                                 '%s[%d]' % (path, item_idx),
                                 '必须是字符串（实际为%s）' % type_name(item))


def check_fanwen_evidence(rule, idx, report):
    """判据 8：范文观察必须有合法证据引用。"""
    refs = rule.get('evidence_refs')
    if not isinstance(refs, list):
        return  # 类型问题已在判据 6 报告
    base = 'rules[%d]' % idx
    if not refs:
        report.error(CONTRACT_LABEL, base + '.evidence_refs',
                     'empty for 范文观察（至少一条证据引用）')
        return
    for ref_idx, ref in enumerate(refs):
        if not isinstance(ref, str):
            continue  # 类型问题已在判据 6 报告
        if not EVIDENCE_RE.match(ref):
            report.error(CONTRACT_LABEL,
                         '%s.evidence_refs[%d]' % (base, ref_idx),
                         '格式不符：%s（应为 S01-P05、S01-P05-P07 '
                         '或 S01-P02→P21）' % fmt(ref))


def check_generic_rule(rule, idx, report):
    """判据 9：通用方法/用户反馈不得伪称范文证据。"""
    base = 'rules[%d]' % idx
    basis_type = rule['basis_type']
    refs = rule.get('evidence_refs')
    if isinstance(refs, list) and refs:
        report.error(CONTRACT_LABEL, base + '.evidence_refs',
                     'must be empty for %s（实际为%s）'
                     % (basis_type, fmt(refs)))
    note = rule.get('basis_note')
    if 'basis_note' not in rule or not isinstance(note, str):
        return  # 缺失或类型问题已在判据 6 报告
    if not note.strip():
        report.error(CONTRACT_LABEL, base + '.basis_note',
                     'empty for %s（必须写明来源性质）' % basis_type)
        return
    match = SAMPLE_CITE_RE.search(note)
    if match:
        report.error(CONTRACT_LABEL, base + '.basis_note',
                     '含样本引用 %s（%s不得伪称范文证据）'
                     % (match.group(0), basis_type))


def check_rules(rules, group_values, report):
    """判据 5、6、8、9 及附带的核心规则检查。"""
    if not isinstance(rules, list):
        report.error(CONTRACT_LABEL, 'rules',
                     '必须是数组（实际为%s）' % type_name(rules))
        return
    if not rules:
        report.error(CONTRACT_LABEL, 'rules', '至少需要一条规则')
        return

    seen = {}
    core_rules = []
    optional_enabled = []
    optional_total = 0
    for idx, rule in enumerate(rules):
        base = 'rules[%d]' % idx
        if not isinstance(rule, dict):
            report.error(CONTRACT_LABEL, base,
                         '必须是 JSON 对象（实际为%s）' % type_name(rule))
            continue

        rule_id = check_rule_id(rule, idx, seen, report)
        check_rule_fields(rule, idx, report)

        feature_group = rule.get('feature_group')
        if isinstance(feature_group, str):
            if group_values is not None and feature_group not in group_values:
                report.error(CONTRACT_LABEL, base + '.feature_group',
                             '%s 不在 feature_config.group_values 内'
                             % fmt(feature_group))
            if feature_group == '核心':
                core_rules.append(rule_id or base)
            if feature_group == '可选':
                optional_total += 1
                if rule.get('default_enabled') is True:
                    optional_enabled.append(rule_id or base)

        basis_type = rule.get('basis_type')
        if isinstance(basis_type, str) and basis_type not in BASIS_TYPES:
            report.error(CONTRACT_LABEL, base + '.basis_type',
                         '%s 不在允许值内（允许 %s）'
                         % (fmt(basis_type), '、'.join(BASIS_TYPES)))

        materials = rule.get('required_materials')
        preparation = rule.get('preparation_action')
        if (isinstance(materials, list) and materials
                and isinstance(preparation, str)
                and not preparation.strip()):
            report.error(CONTRACT_LABEL, base + '.preparation_action',
                         'empty for required_materials'
                         '（required_materials 非空，准备动作不得为空）')

        if basis_type == '范文观察':
            check_fanwen_evidence(rule, idx, report)
        elif basis_type in ('通用执行方法', '用户反馈适配'):
            check_generic_rule(rule, idx, report)

    if not core_rules:
        report.error(CONTRACT_LABEL, 'rules',
                     '至少需要一条 feature_group 为 "核心" 的规则')
    if optional_total and len(optional_enabled) == optional_total:
        report.warn('可选规则全部默认启用（%s）；规格建议可选动作通常'
                    '不默认开启。' % '、'.join(optional_enabled))


def path_problem(value, pkg_dir):
    """判据 7：路径必须是包内相对路径，返回问题描述或 None。"""
    normalized = value.replace('\\', '/')
    if os.path.isabs(value) or DRIVE_RE.match(value) or normalized.startswith('/'):
        return '不得使用绝对路径：%s' % value
    parts = [p for p in normalized.split('/') if p not in ('', '.')]
    if '..' in parts:
        return '不得包含 .. 跳转：%s' % value
    if not is_within(pkg_dir, os.path.join(pkg_dir, value)):
        return '解析后不在包目录内：%s' % value
    return None


def is_within(root, path):
    root_real = os.path.normcase(os.path.realpath(root))
    path_real = os.path.normcase(os.path.realpath(path))
    try:
        return os.path.commonpath([root_real, path_real]) == root_real
    except ValueError:
        return False


def check_resources(resources, pkg_dir, report):
    """判据 7：组件引用包内有效，执行依赖为空。"""
    if not isinstance(resources, dict):
        report.error(CONTRACT_LABEL, 'resources',
                     '必须是 JSON 对象（实际为%s）' % type_name(resources))
        return

    for key in ('preparation', 'rewriting'):
        path = 'resources.%s' % key
        if key not in resources:
            report.error(CONTRACT_LABEL, path, 'missing')
            continue
        value = resources[key]
        if not is_text(value):
            report.error(CONTRACT_LABEL, path,
                         'empty（必须是非空字符串路径）')
            continue
        value = value.strip()
        problem = path_problem(value, pkg_dir)
        if problem:
            report.error(CONTRACT_LABEL, path, problem)
            continue
        if not os.path.isfile(os.path.join(pkg_dir, value)):
            report.error(CONTRACT_LABEL, path,
                         '引用的文件不存在：%s' % value)

    path = 'resources.external_dependencies'
    if 'external_dependencies' not in resources:
        report.error(CONTRACT_LABEL, path, 'missing')
    elif not isinstance(resources['external_dependencies'], list):
        report.error(CONTRACT_LABEL, path,
                     '必须是数组（实际为%s）'
                     % type_name(resources['external_dependencies']))
    elif resources['external_dependencies']:
        report.error(CONTRACT_LABEL, path,
                     'non-empty（必须为空数组；实际为%s）'
                     % fmt(resources['external_dependencies']))


def check_sample_fields(identity, report):
    """判据 10 前半：sample_count 与 sample_ids 等长且唯一。"""
    count = identity.get('sample_count')
    ids = identity.get('sample_ids')
    if 'sample_count' not in identity:
        report.error(CONTRACT_LABEL, 'identity.sample_count', 'missing')
    elif not is_int(count):
        report.error(CONTRACT_LABEL, 'identity.sample_count',
                     '必须是整数（实际为%s）' % type_name(count))
    elif count < 1:
        report.error(CONTRACT_LABEL, 'identity.sample_count',
                     '必须 ≥ 1（实际为%d）' % count)

    if 'sample_ids' not in identity:
        report.error(CONTRACT_LABEL, 'identity.sample_ids', 'missing')
        return None
    if not isinstance(ids, list):
        report.error(CONTRACT_LABEL, 'identity.sample_ids',
                     '必须是数组（实际为%s）' % type_name(ids))
        return None

    seen = {}
    for idx, sample_id in enumerate(ids):
        path = 'identity.sample_ids[%d]' % idx
        if not isinstance(sample_id, str):
            report.error(CONTRACT_LABEL, path,
                         '必须是字符串（实际为%s）' % type_name(sample_id))
            continue
        if not SAMPLE_ID_RE.match(sample_id):
            report.error(CONTRACT_LABEL, path,
                         '格式不符：%s（应为 S 加两位数字，如 S01）'
                         % fmt(sample_id))
        if sample_id in seen:
            report.error(CONTRACT_LABEL, path,
                         '%s 重复（另见 identity.sample_ids[%d]）'
                         % (fmt(sample_id), seen[sample_id]))
        else:
            seen[sample_id] = idx

    if is_int(count) and len(ids) != count:
        report.error(CONTRACT_LABEL, 'identity.sample_count',
                     '%d 与 sample_ids 数量 %d 不一致' % (count, len(ids)))
    return ids


def check_length_policy(length_policy, sample_ids, report):
    """判据 10 后半及规格 3.2 的 target_adaptation。"""
    if not isinstance(length_policy, dict):
        report.error(CONTRACT_LABEL, 'length_policy',
                     '必须是 JSON 对象（实际为%s）' % type_name(length_policy))
        return

    if 'target_adaptation' not in length_policy:
        report.error(CONTRACT_LABEL, 'length_policy.target_adaptation',
                     'missing')
    elif not is_text(length_policy['target_adaptation']):
        report.error(CONTRACT_LABEL, 'length_policy.target_adaptation',
                     'empty（必须是非空字符串）')

    path = 'length_policy.sample_observations'
    if 'sample_observations' not in length_policy:
        report.error(CONTRACT_LABEL, path, 'missing')
        return
    observations = length_policy['sample_observations']
    if not isinstance(observations, list):
        report.error(CONTRACT_LABEL, path,
                     '必须是数组（实际为%s）' % type_name(observations))
        return
    if not observations:
        report.error(CONTRACT_LABEL, path, '必须是非空数组')
        return

    known = None
    if isinstance(sample_ids, list):
        known = set(sid for sid in sample_ids if isinstance(sid, str))
    for idx, item in enumerate(observations):
        base = '%s[%d]' % (path, idx)
        if not isinstance(item, dict):
            report.error(CONTRACT_LABEL, base,
                         '必须是 JSON 对象（实际为%s）' % type_name(item))
            continue

        if 'sample_id' not in item:
            report.error(CONTRACT_LABEL, base + '.sample_id', 'missing')
        elif not is_text(item['sample_id']):
            report.error(CONTRACT_LABEL, base + '.sample_id',
                         'empty（必须是非空字符串）')
        elif known is not None and item['sample_id'].strip() not in known:
            report.error(CONTRACT_LABEL, base + '.sample_id',
                         '%s not in sample_ids' % item['sample_id'].strip())

        for key in ('body_chars_non_whitespace', 'paragraph_count'):
            field_path = '%s.%s' % (base, key)
            if key not in item:
                report.error(CONTRACT_LABEL, field_path, 'missing')
            elif not is_int(item[key]):
                report.error(CONTRACT_LABEL, field_path,
                             '必须是整数（实际为%s）' % type_name(item[key]))
            elif item[key] < 0:
                report.error(CONTRACT_LABEL, field_path,
                             '必须 ≥ 0（实际为%d）' % item[key])

        if 'note' not in item:
            report.error(CONTRACT_LABEL, base + '.note', 'missing')
        elif not isinstance(item['note'], str):
            report.error(CONTRACT_LABEL, base + '.note',
                         '必须是字符串（实际为%s）' % type_name(item['note']))


def check_contract(contract, pkg_dir, dir_name, entry_name, report):
    """判据 3—10 的 JSON 结构检查入口。"""
    if not isinstance(contract, dict):
        report.error(CONTRACT_LABEL, '',
                     '顶层必须是 JSON 对象（实际为%s）'
                     % type_name(contract))
        return

    for key in TOP_KEYS:
        if key not in contract:
            report.error(CONTRACT_LABEL, key, 'missing')

    if 'schema_version' in contract and contract['schema_version'] != '1.0':
        report.error(CONTRACT_LABEL, 'schema_version',
                     '必须为 "1.0"（实际为%s）'
                     % fmt(contract['schema_version']))

    if 'identity' in contract:
        check_identity(contract['identity'], dir_name, entry_name, report)

    group_values = None
    if 'feature_config' in contract:
        group_values = check_feature_config(contract['feature_config'], report)

    if 'rules' in contract:
        check_rules(contract['rules'], group_values, report)

    if 'resources' in contract:
        check_resources(contract['resources'], pkg_dir, report)

    sample_ids = None
    identity = contract.get('identity')
    if isinstance(identity, dict):
        sample_ids = check_sample_fields(identity, report)
    if 'length_policy' in contract:
        check_length_policy(contract['length_policy'], sample_ids, report)


def print_summary(contract):
    """通过时输出简要统计。"""
    identity = contract['identity']
    rules = contract['rules']
    basis = Counter(rule['basis_type'] for rule in rules)
    groups = Counter(rule['feature_group'] for rule in rules)
    observations = contract['length_policy']['sample_observations']

    print('  身份：%s（%s），%s %s'
          % (identity['style_id'], identity['display_name'],
             identity['style_version'], identity['status']))
    print('  规则：%d 条；核心 %d、条件 %d、可选 %d；'
          '范文观察 %d、通用执行方法 %d、用户反馈适配 %d'
          % (len(rules), groups.get('核心', 0), groups.get('条件', 0),
             groups.get('可选', 0), basis.get('范文观察', 0),
             basis.get('通用执行方法', 0), basis.get('用户反馈适配', 0)))
    print('  样本：%d 个（%s）；篇幅观察 %d 条'
          % (identity['sample_count'], '、'.join(identity['sample_ids']),
             len(observations)))
    print('  资源：%s、%s 均在包内；external_dependencies 为空'
          % (contract['resources']['preparation'],
             contract['resources']['rewriting']))


def main():
    if len(sys.argv) != 2:
        print('用法：python package_check.py <文风包目录>', file=sys.stderr)
        return 2
    pkg_dir = sys.argv[1]
    if not os.path.exists(pkg_dir):
        print('错误：目录不存在：%s' % pkg_dir, file=sys.stderr)
        return 2
    if not os.path.isdir(pkg_dir):
        print('错误：不是目录：%s' % pkg_dir, file=sys.stderr)
        return 2

    report = Report()
    print('检查文风包：%s' % os.path.abspath(pkg_dir))
    paths = check_components(pkg_dir, report)

    entry_name = None
    if os.path.isfile(paths[SKILL_LABEL]):
        entry_name = check_skill_md(paths[SKILL_LABEL], report)

    loaded, contract = False, None
    if os.path.isfile(paths[CONTRACT_LABEL]):
        loaded, contract = load_contract(paths[CONTRACT_LABEL], report)
    if loaded:
        dir_name = os.path.basename(os.path.abspath(pkg_dir))
        check_contract(contract, pkg_dir, dir_name, entry_name, report)

    if report.errors:
        print('发现 %d 个问题：' % len(report.errors))
        for idx, item in enumerate(report.errors, 1):
            print('  %d. %s' % (idx, item))
        for warning in report.warnings:
            print('  提示：%s' % warning)
        print('结果：不通过。')
        return 1

    for warning in report.warnings:
        print('提示：%s' % warning)
    print_summary(contract)
    print('结果：通过。')
    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    sys.exit(main())
