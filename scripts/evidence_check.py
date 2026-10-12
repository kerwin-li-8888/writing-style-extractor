#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence_check.py —— 证据引用回查

用法：
    python evidence_check.py <证据表.md> <分析文本目录>

扫描证据表（及规则包、开发验证记录等 markdown）中的 S{nn}-P{nn} 式引用，
逐条回查分析文本目录中对应样本的【Pnn】段落标记是否存在。

支持的形式：
    S01-P05            单点引用
    S01-P55-P61        区间引用（端点逐个核验）
    S01-P02→P12-P21    结构跨度引用（链上编号逐个核验）

退出码：0 = 全部通过；1 = 存在查不到的引用；2 = 输入错误。
本脚本只核验"引用可定位"，不判断证据是否支持结论。
"""
import glob
import os
import re
import sys

CITE_RE = re.compile(r'S(\d+)((?:-P(\d+))(?:[-–—→]P(\d+))*)')
FILE_RE = re.compile(r'^S(\d+)-.*\.md$')
PARA_RE = re.compile(r'(?m)^【P(\d+)】')


def load_samples(dirpath):
    samples = {}
    for path in glob.glob(os.path.join(dirpath, '*.md')):
        name = os.path.basename(path)
        m = FILE_RE.match(name)
        if not m:
            continue
        with open(path, 'r', encoding='utf-8-sig') as f:
            text = f.read()
        p_nums = set(int(x) for x in PARA_RE.findall(text))
        samples[int(m.group(1))] = {'file': name, 'paras': p_nums}
    return samples


def main():
    if len(sys.argv) != 3:
        print('用法：python evidence_check.py <证据表.md> <分析文本目录>',
              file=sys.stderr)
        sys.exit(2)
    ev_path, ana_dir = sys.argv[1], sys.argv[2]
    if not os.path.isfile(ev_path):
        print('错误：找不到 %s' % ev_path, file=sys.stderr)
        sys.exit(2)
    samples = load_samples(ana_dir)
    if not samples:
        print('错误：%s 下没有 S*.md 分析文本' % ana_dir, file=sys.stderr)
        sys.exit(2)

    with open(ev_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    total = 0
    broken = []
    for lineno, line in enumerate(lines, 1):
        for m in CITE_RE.finditer(line):
            s_num = int(m.group(1))
            p_nums = [int(x) for x in re.findall(r'P(\d+)', m.group(2))]
            total += 1
            if s_num not in samples:
                broken.append((lineno, m.group(0),
                               '样本 S%02d 不存在（分析文本共 %d 篇）'
                               % (s_num, len(samples))))
                continue
            for p in p_nums:
                if p not in samples[s_num]['paras']:
                    broken.append((lineno, m.group(0),
                                   '%s 中没有【P%d】段落'
                                   % (samples[s_num]['file'], p)))

    print('引用回查：%s' % os.path.basename(ev_path))
    print('分析文本：%d 篇（S01-S%02d）' % (len(samples), max(samples)))
    print('引用总数：%d' % total)
    if broken:
        print('查不到的引用：%d 处' % len(broken))
        for lineno, cite, reason in broken:
            print('  第 %d 行  %s  ← %s' % (lineno, cite, reason))
        print()
        print('处理：逐条修改或删除，不得保留无法回查的证据。')
        sys.exit(1)
    print('结果：全部通过。')
    sys.exit(0)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
