#!/usr/bin/env python3
"""
Markdown 链接检查器
扫描仓库中所有 .md 文件，检查相对路径链接是否有效。

用法:
    python3 scripts/check_links.py          # 检查全仓库
    python3 scripts/check_links.py --strict  # 有断链时退出码1
    python3 scripts/check_links.py README.md # 检查单个文件

可作为 pre-commit hook 使用:
    cp scripts/check_links.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""

import os
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict


def check_markdown_links(base_dir: str, file_filter: str = None, strict: bool = False) -> int:
    """检查所有 Markdown 文件的链接完整性，返回断链数量。"""
    base = Path(base_dir).resolve()
    total_links = 0
    broken_count = 0
    broken_by_file = defaultdict(list)

    md_files = []
    for root, dirs, files in os.walk(base):
        # 跳过 .git, node_modules
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__')]
        for f in files:
            if f.endswith('.md'):
                md_files.append(Path(root) / f)

    if file_filter:
        md_files = [f for f in md_files if file_filter in str(f)]

    md_files.sort()

    for fp in md_files:
        rel_path = fp.relative_to(base)
        try:
            content = fp.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        # 移除代码块（```包裹的内容）
        content_no_code = re.sub(r'```[\s\S]*?```', '', content)
        # 移除行内代码
        content_no_code = re.sub(r'`[^`]*`', '', content_no_code)

        # 匹配尖括号链接 [text](<url>)
        angle_links = re.findall(r'\[([^\]]*)\]\(<([^>]+)>\)', content_no_code)
        for text, link in angle_links:
            total_links += 1
            if link.startswith('http') or link.startswith('#'):
                continue
            link_clean = link.split('#')[0].replace('%20', ' ')
            if not link_clean:
                continue
            target = (fp.parent / link_clean).resolve()
            if not target.exists():
                broken_count += 1
                broken_by_file[str(rel_path)].append(link)

        # 移除已匹配的尖括号链接，再匹配普通链接
        content_remaining = re.sub(r'\[([^\]]*)\]\(<[^>]+>\)', '', content_no_code)
        normal_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content_remaining)
        for text, link in normal_links:
            if link.startswith('http') or link.startswith('#'):
                continue
            total_links += 1
            link_clean = link.split('#')[0].replace('%20', ' ')
            if not link_clean:
                continue
            target = (fp.parent / link_clean).resolve()
            if not target.exists():
                broken_count += 1
                broken_by_file[str(rel_path)].append(link)

    # 输出报告
    print(f"\n{'='*60}")
    print(f"  Markdown 链接检查报告")
    print(f"{'='*60}")
    print(f"  扫描文件数: {len(md_files)}")
    print(f"  检查链接数: {total_links}")
    print(f"  断链数量:   {broken_count}")

    if broken_count > 0:
        print(f"\n  断链详情:")
        for filepath, links in sorted(broken_by_file.items()):
            print(f"\n  {filepath}:")
            for link in links:
                print(f"    -> {link}")
    else:
        print(f"\n  ✅ 全部链接有效")

    print(f"\n{'='*60}")

    if strict and broken_count > 0:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description='Markdown 链接检查器')
    parser.add_argument('path', nargs='?', default='.', help='检查路径（默认当前目录）')
    parser.add_argument('--filter', dest='filter', help='只检查文件名包含此字符串的文件')
    parser.add_argument('--strict', action='store_true', help='有断链时返回非零退出码')
    args = parser.parse_args()

    exit_code = check_markdown_links(args.path, args.filter, args.strict)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
