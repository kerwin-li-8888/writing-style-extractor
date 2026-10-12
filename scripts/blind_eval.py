#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blind_eval.py —— 盲评打乱与解盲计分

用法：
    python blind_eval.py shuffle <输出目录> [--out 盲评包目录] [--seed N]
    python blind_eval.py tally <盲评包目录>

输出目录中的文章文件命名约定（生成时按此保存）：
    开发试验：  T{任务号}-{组}.md        如 T1-A.md  T3-D.md   （组 = A/B/C/D）
    独立复测：  T{任务号}-{组}{次}.md    如 T1-D1.md T1-B2.md  （组 = B/D，各两次）

shuffle：
    把所有输出打乱复制为 eval-{NN}.md，生成密钥.json（评分完成前不得打开）
    与空白评分表.csv（五维度 1-5 分 + 事实失真 0/1 + 文本依据）。

tally：
    读入填好的评分表.csv 与密钥.json，解盲后输出：分组五维度均值、
    配对胜负（文风接近为主维度）、验收门槛核对（独立复测模式）。
    结果写入盲评包目录下 评分汇总.md。

评分约定：1-5 分，5 为最好；修改成本 5 = 几乎不用改；事实失真 1 = 有失真。
"""
import argparse
import csv
import glob
import json
import os
import random
import re
import sys
import time

NAME_RE = re.compile(r'^T(\d+)-([A-Z])(\d?)\.md$')
DIMENSIONS = ['内容忠实', '文风接近', '自然可读', '表达独立', '修改成本']
CANDIDATE_GROUPS_DEV = ['C', 'D']
CANDIDATE_GROUPS_RETEST = ['D']


def scan_outputs(dirpath):
    entries = []
    for path in sorted(glob.glob(os.path.join(dirpath, '*.md'))):
        m = NAME_RE.match(os.path.basename(path))
        if m:
            entries.append({'path': path,
                            'task': int(m.group(1)),
                            'group': m.group(2),
                            'run': int(m.group(3)) if m.group(3) else None})
    return entries


def is_retest(entries):
    return any(e['run'] is not None for e in entries)


def cmd_shuffle(args):
    entries = scan_outputs(args.dir)
    if not entries:
        print('错误：%s 下没有符合 T{n}-{组}[{次}].md 命名的输出' % args.dir,
              file=sys.stderr)
        sys.exit(2)
    seed = args.seed if args.seed is not None else random.randrange(10 ** 6)
    rng = random.Random(seed)
    shuffled = entries[:]
    rng.shuffle(shuffled)

    out_dir = args.out or (args.dir.rstrip('\\/') + '_盲评包')
    os.makedirs(out_dir, exist_ok=True)

    mapping = {}
    for idx, e in enumerate(shuffled, 1):
        eval_id = 'eval-%02d' % idx
        with open(e['path'], 'r', encoding='utf-8-sig') as f:
            content = f.read()
        with open(os.path.join(out_dir, eval_id + '.md'), 'w',
                  encoding='utf-8') as f:
            f.write(content)
        mapping[eval_id] = {'task': e['task'], 'group': e['group'],
                            'run': e['run']}

    key = {'seed': seed, 'created': time.strftime('%Y-%m-%d %H:%M:%S'),
           'mode': '独立复测' if is_retest(entries) else '开发试验',
           'mapping': mapping}
    with open(os.path.join(out_dir, '密钥.json'), 'w', encoding='utf-8') as f:
        json.dump(key, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, '评分表.csv'), 'w', encoding='utf-8-sig',
              newline='') as f:
        w = csv.writer(f)
        w.writerow(['eval_id'] + DIMENSIONS + ['事实失真', '文本依据'])
        for eval_id in sorted(mapping):
            w.writerow([eval_id, '', '', '', '', '', '', ''])

    print('盲评包已生成：%s（模式：%s，seed=%d，共 %d 篇）'
          % (out_dir, key['mode'], seed, len(mapping)))
    print('下一步：把 eval-*.md 与评分表.csv 交给评审；'
          '评分完成前不要打开 密钥.json。')


def mean(values):
    return sum(values) / len(values) if values else float('nan')


def load_scores(out_dir):
    key_path = os.path.join(out_dir, '密钥.json')
    csv_path = os.path.join(out_dir, '评分表.csv')
    for p in (key_path, csv_path):
        if not os.path.isfile(p):
            print('错误：缺少 %s' % p, file=sys.stderr)
            sys.exit(2)
    with open(key_path, 'r', encoding='utf-8') as f:
        key = json.load(f)
    scores = {}
    missing = []
    bad = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            eval_id = (row.get('eval_id') or '').strip()
            if not eval_id:
                continue
            try:
                vals = {d: float(row[d]) for d in DIMENSIONS}
                distortion = (row.get('事实失真') or '').strip()
                if distortion not in ('0', '1'):
                    bad.append((eval_id, '事实失真须为 0 或 1'))
                    continue
                vals['事实失真'] = int(distortion)
                scores[eval_id] = vals
            except (ValueError, KeyError) as exc:
                bad.append((eval_id, '五维度须为 1-5 数字（%s）' % exc))
    for eval_id in key['mapping']:
        if eval_id not in scores:
            missing.append(eval_id)
    return key, scores, missing, bad


def cmd_tally(args):
    key, scores, missing, bad = load_scores(args.dir)
    if bad:
        print('评分表存在无效数据：')
        for eval_id, reason in bad:
            print('  %s：%s' % (eval_id, reason))
        sys.exit(1)
    if missing:
        print('评分表未填完，缺少：%s' % '、'.join(missing))
        sys.exit(1)

    mapping = key['mapping']
    retest = key['mode'] == '独立复测'
    tasks = sorted(set(v['task'] for v in mapping.values()))
    groups = sorted(set(v['group'] for v in mapping.values()))

    lines = []
    lines.append('# 盲评评分汇总（%s 模式）' % key['mode'])
    lines.append('')
    lines.append('> 解盲时间：%s　主判定维度：文风接近。'
                 '事实失真单列，不允许由其他高分抵消。'
                 % time.strftime('%Y-%m-%d %H:%M:%S'))

    # 分组均值表
    lines.append('')
    lines.append('## 分组五维度均值')
    lines.append('')
    lines.append('| 组 | 篇数 | ' + ' | '.join(DIMENSIONS) + ' | 事实失真篇数 |')
    lines.append('|---|---|' + '---|' * (len(DIMENSIONS) + 1))
    group_scores = {}
    for g in groups:
        rows = [scores[k] for k, v in mapping.items() if v['group'] == g]
        group_scores[g] = rows
        lines.append('| %s | %d | %s | %d |' % (
            g, len(rows),
            ' | '.join('%.2f' % mean([r[d] for r in rows]) for d in DIMENSIONS),
            sum(r['事实失真'] for r in rows)))
    lines.append('')

    # 配对比较（主维度：文风接近）
    pair_defs = ([(('D', None), ('B', None))] if retest
                 else [(('C', None), ('A', None)),
                       (('D', None), ('B', None)),
                       (('D', None), ('C', None))])

    def find(task, group, run):
        for k, v in mapping.items():
            if v['task'] == task and v['group'] == group and v['run'] == run:
                return k
        return None

    lines.append('## 配对比较（按文风接近分）')
    lines.append('')
    results = {pd: {'win': 0, 'tie': 0, 'lose': 0, 'detail': []}
               for pd in pair_defs}
    for task in tasks:
        runs = ([1, 2] if retest else [None])
        for run in runs:
            for (g_x, _), (g_y, _) in pair_defs:
                kx = find(task, g_x, run)
                ky = find(task, g_y, run)
                sx = scores[kx]['文风接近']
                sy = scores[ky]['文风接近']
                tag = '任务%d' % task + ('第%d次' % run if run else '')
                if sx > sy:
                    verdict, r = '%s 胜' % g_x, 'win'
                elif sx < sy:
                    verdict, r = '%s 胜' % g_y, 'lose'
                else:
                    verdict, r = '平局', 'tie'
                results[((g_x, None), (g_y, None))][r] += 1
                results[((g_x, None), (g_y, None))]['detail'].append(
                    '%s：%s %g vs %s %g → %s' % (tag, g_x, sx, g_y, sy, verdict))
    for (g_x, _), (g_y, _) in pair_defs:
        res = results[((g_x, None), (g_y, None))]
        lines.append('- **%s vs %s**：%d 胜 / %d 平 / %d 负' % (
            g_x, g_y, res['win'], res['tie'], res['lose']))
        for d in res['detail']:
            lines.append('  - %s' % d)
    lines.append('')

    report = '\n'.join(lines)

    # 门槛核对（独立复测模式）
    if retest:
        d_rows = group_scores.get('D', [])
        b_rows = group_scores.get('B', [])
        res = results[((('D', None), ('B', None)))]
        cand_groups = CANDIDATE_GROUPS_RETEST
        distortion_n = sum(r['事实失真'] for g in cand_groups
                           for r in group_scores.get(g, []))
        total_pairs = res['win'] + res['tie'] + res['lose']
        consec = []
        for task in tasks:
            losses = []
            for run in (1, 2):
                kx = find(task, 'D', run)
                ky = find(task, 'B', run)
                losses.append(scores[kx]['文风接近'] < scores[ky]['文风接近'])
            if all(losses):
                consec.append('任务%d' % task)
        consec_note = ('（违反：%s）' % '、'.join(consec)) if consec else ''
        checks = [
            ('所有候选输出无关键事实失真', distortion_n == 0),
            ('%d 次比较中规则方案至少 4 次文风获胜' % total_pairs,
             res['win'] >= 4),
            ('任一任务未出现规则方案连续两次落败' + consec_note, not consec),
            ('自然可读性没有整体下降',
             mean([r['自然可读'] for r in d_rows]) >= mean([r['自然可读'] for r in b_rows])),
            ('修改成本没有整体上升',
             mean([r['修改成本'] for r in d_rows]) >= mean([r['修改成本'] for r in b_rows])),
        ]
        report += '## 验收门槛核对\n\n| 门槛 | 达成 |\n|---|---|\n'
        for label, ok in checks:
            report += '| %s | %s |\n' % (label, '✅' if ok else '❌')
        report += ('\n> 五项全部通过 = 可用候选版本；冻结为正式基线仍需用户明示确认。\n')
    else:
        report += ('> 开发试验模式：门槛核对仅在独立复测（7.3/7.4）适用，'
                   '此处只看三组对比结论与修订方向。\n')

    out_path = os.path.join(args.dir, '评分汇总.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report + '\n')
    print(report)
    print('\n汇总已写入：%s' % out_path)


def main():
    ap = argparse.ArgumentParser(description='盲评打乱与解盲计分')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('shuffle', help='打乱输出，生成盲评包')
    p1.add_argument('dir', help='试验输出目录（T{n}-{组}[{次}].md）')
    p1.add_argument('--out', default=None, help='盲评包目录（默认加后缀 _盲评包）')
    p1.add_argument('--seed', type=int, default=None, help='随机种子')
    p2 = sub.add_parser('tally', help='解盲计分，核对门槛')
    p2.add_argument('dir', help='盲评包目录（含 密钥.json 与填好的 评分表.csv）')
    args = ap.parse_args()
    if args.cmd == 'shuffle':
        cmd_shuffle(args)
    else:
        cmd_tally(args)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
