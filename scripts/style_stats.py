#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_stats.py —— 文风统计签名

用法：
    python style_stats.py <分析文本目录或文件...> [--patterns "正则1,正则2"]

对带【Pnn】段落编号的分析文本计算统计口径：总段数、总字符、单句段率、
平均段长、平均句长、句长变异系数、极短段率，以及默认口径
（"我觉得/我认为"、含"你"/"我"段率、"。。。"、问号连用、加粗、小标题）。
--patterns 可追加作者特有口径（如 "对吧,就像这样"），追加列按出现次数计。

输出 markdown 表，可直接贴进证据表"统计口径"一节。

口径说明：
- 段落 = 分析文本中的【Pnn】块；P01（标题行）计入统计。
- 字符数不含任何空白；句读终止符为 。！？…?!（连用算一次，如 。。。 算一句终止）。
- 单句段 = 句读数 ≤1 的段落。
- 极短段 = 不含空白后 ≤8 字的段落。
"""
import argparse
import glob
import os
import re
import sys

TERM_RE = re.compile(r'[。！？…?!]+')
# 纯标点/引号/空白片段（如句号后的收尾引号 " ）不构成句子
NON_WORD_RE = re.compile(
    r'[\s\u3000"“”「」『』（）()《》〈〉【】\[\]·—\-~～*#>@，。！？、；：:?!,;.\'‘’]+')
PARA_SPLIT_RE = re.compile(r'(?m)(?=^【P\d+】)')
PARA_HEAD_RE = re.compile(r'(?m)^【P(\d+)】')


def parse_paragraphs(text):
    """返回 [(段落编号, 去标记正文)]；正文内部换行保留原样。"""
    paras = []
    for chunk in PARA_SPLIT_RE.split(text):
        m = PARA_HEAD_RE.match(chunk)
        if not m:
            continue
        body = chunk[m.end():]
        paras.append((int(m.group(1)), body))
    return paras


def sentence_lengths(body):
    """返回该段各句的字符长（不含空白；终止符连用算一次）。

    句号后孤立的收尾引号等纯标点片段不算句子：
    "让最终答案真正对我有用。" 只算一句，不是两句。
    """
    compact = ''.join(body.split())
    lens = []
    for seg in TERM_RE.split(compact):
        if NON_WORD_RE.sub('', seg):
            lens.append(len(seg))
    if not lens and compact:
        lens.append(len(compact))  # 全段无终止符（标题、短语段）算一句
    return lens


def cv(values):
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    if mean == 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return (var ** 0.5) / mean


def collect_files(args_list):
    files = []
    for arg in args_list:
        if os.path.isdir(arg):
            files.extend(glob.glob(os.path.join(arg, 'S*.md')))
        elif os.path.exists(arg):
            files.append(arg)
        else:
            print('警告：路径不存在，跳过 %s' % arg, file=sys.stderr)
    return sorted(set(files))


def stats_one(path, extra_patterns):
    with open(path, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    paras = parse_paragraphs(text)
    if not paras:
        return None
    # 计数口径基于段落正文，不含文件头的说明区
    para_text = '\n'.join(body for _no, body in paras)

    para_lens = []
    single = 0
    tiny = 0
    sent_lens = []
    has_you = 0
    has_wo = 0
    headings = 0
    for _no, body in paras:
        compact = ''.join(body.split())
        para_lens.append(len(compact))
        if len(compact) <= 8:
            tiny += 1
        sl = sentence_lengths(body)
        if len(sl) <= 1:
            single += 1
        sent_lens.extend(sl)
        if '你' in body:
            has_you += 1
        if '我' in body:
            has_wo += 1
        if body.strip().startswith('#'):
            headings += 1

    n = len(paras)
    row = {
        '文件': os.path.basename(path),
        '总段数': n,
        '总字符': sum(para_lens),
        '单句段率': single / n,
        '平均段长': sum(para_lens) / n,
        '平均句长': sum(sent_lens) / max(1, len(sent_lens)),
        '句长CV': cv(sent_lens),
        '极短段': tiny,
        '我觉得/我认为': len(re.findall(r'我觉得|我认为', para_text)),
        '含你段率': has_you / n,
        '含我段率': has_wo / n,
        '。。。': len(re.findall(r'。{3,}', para_text)),
        '问号连用': len(re.findall(r'[？?]{2,}', para_text)),
        '加粗': para_text.count('**') // 2,
        '小标题': headings,
    }
    for label, pat in extra_patterns:
        row[label] = len(re.findall(pat, para_text))
    return row


def fmt(v, pct=False):
    if pct:
        return '%.0f%%' % (v * 100)
    return '%.1f' % v


def main():
    ap = argparse.ArgumentParser(description='文风统计签名（分析文本口径）')
    ap.add_argument('paths', nargs='+', help='分析文本目录或文件')
    ap.add_argument('--patterns', default='',
                    help='追加计数口径，逗号分隔，如 "对吧,就像这样"')
    args = ap.parse_args()

    extra_patterns = []
    if args.patterns:
        for piece in re.split(r'[,，]', args.patterns):
            piece = piece.strip()
            if piece:
                extra_patterns.append((piece, re.escape(piece)))

    files = collect_files(args.paths)
    if not files:
        print('错误：没有找到分析文本（目录下应存在 S*.md）', file=sys.stderr)
        sys.exit(2)

    rows = []
    for p in files:
        r = stats_one(p, extra_patterns)
        if r is None:
            print('警告：%s 中没有【Pnn】段落标记，跳过' % os.path.basename(p),
                  file=sys.stderr)
        else:
            rows.append(r)

    pct_cols = ['单句段率', '含你段率', '含我段率']
    int_cols = ['总段数', '总字符', '极短段', '我觉得/我认为', '。。。', '问号连用', '加粗', '小标题']
    float_cols = ['平均段长', '平均句长', '句长CV']
    cols = (['文件'] + int_cols[:2] + ['单句段率'] + float_cols + ['极短段']
            + int_cols[3:] + [p[0] for p in extra_patterns])

    out = []
    out.append('| ' + ' | '.join(cols) + ' |')
    out.append('|' + '---|' * len(cols))
    for r in rows:
        cells = []
        for c in cols:
            v = r[c]
            if c == '文件':
                cells.append(v)
            elif c in pct_cols:
                cells.append(fmt(v, pct=True))
            elif c in int_cols or c in [p[0] for p in extra_patterns]:
                cells.append(str(v))
            else:
                cells.append(fmt(v))
        out.append('| ' + ' | '.join(cells) + ' |')

    # 汇总行：比率与均值给 min-max 范围与均值
    agg = []
    for c in cols[1:]:
        vals = [r[c] for r in rows]
        if c in pct_cols:
            agg.append('%s-%s（均 %s）' % (fmt(min(vals), True), fmt(max(vals), True),
                                           fmt(sum(vals) / len(vals), True)))
        elif c in int_cols or c in [p[0] for p in extra_patterns]:
            agg.append('%d-%d' % (min(vals), max(vals)))
        else:
            agg.append('%s-%s' % (fmt(min(vals)), fmt(max(vals))))
    out.append('| **汇总(%d 篇)** | ' % len(rows) + ' | '.join(agg) + ' |')

    print('\n'.join(out))
    print()
    print('> 口径：字符不含空白；终止符 。！？…?! 连用算一次；P01 标题行计入；'
          '极短段 = ≤8 字；单句段 = 句读 ≤1。')


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
