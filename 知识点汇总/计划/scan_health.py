#!/usr/bin/env python3
"""
知识库健康度扫描脚本
用途：被cron job调用，扫描知识库状态，输出健康度报告
退出码：0=健康，1=有问题需关注
"""

import os, re, sys, json
from datetime import datetime

BASE = "/Users/ymh_sirius/001_File/003soft/Obsidian/ai_prompt/cursor_prompt/知识点汇总"
EXCLUDE = {".idea", ".obsidian", "计划", "99_计划"}

def scan():
    dirs = sorted([d for d in os.listdir(BASE) 
                   if os.path.isdir(os.path.join(BASE, d)) and d not in EXCLUDE])
    
    report = {
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_dirs": len(dirs),
        "total_files": 0,
        "total_size_kb": 0,
        "thin_files": [],
        "empty_dirs": [],
        "naming_issues": [],
        "dir_stats": []
    }
    
    for dir_name in dirs:
        dir_path = os.path.join(BASE, dir_name)
        
        all_files = []
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith('.md'):
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, dir_path)
                    all_files.append({"name": f, "rel": rel, "size": os.path.getsize(fp)})
        
        non_readme = [f for f in all_files if f["name"] != "README.md"]
        dir_size = sum(f["size"] for f in all_files)
        report["total_files"] += len(all_files)
        report["total_size_kb"] += dir_size // 1024
        
        # 偏薄文件检测
        for f in non_readme:
            if f["size"] < 5000:
                report["thin_files"].append({
                    "dir": dir_name,
                    "file": f["rel"],
                    "size_kb": f["size"] // 1024
                })
        
        # 空目录检测
        if len(non_readme) == 0:
            report["empty_dirs"].append(dir_name)
        
        # 编号检测
        root_nums = []
        for f in all_files:
            if f["rel"] == f["name"]:
                m = re.match(r'^(\d+)[_.]', f["name"])
                if m:
                    root_nums.append(int(m.group(1)))
        if root_nums:
            root_nums.sort()
            max_n = max(root_nums)
            missing = [i for i in range(1, max_n+1) if i not in set(root_nums)]
            if missing:
                report["naming_issues"].append({
                    "dir": dir_name,
                    "missing": missing
                })
            if 0 in root_nums:
                report["naming_issues"].append({
                    "dir": dir_name,
                    "issue": "编号从0开始"
                })
        
        report["dir_stats"].append({
            "dir": dir_name,
            "files": len(all_files),
            "size_kb": dir_size // 1024,
            "thin_count": len([f for f in non_readme if f["size"] < 5000])
        })
    
    return report

if __name__ == "__main__":
    report = scan()
    
    # 输出摘要
    print(f"扫描时间: {report['scan_time']}")
    print(f"知识库: {report['total_dirs']}个目录, {report['total_files']}篇文档, {report['total_size_kb']}KB")
    print(f"偏薄文件: {len(report['thin_files'])}个")
    print(f"空目录: {len(report['empty_dirs'])}个")
    print(f"编号问题: {len(report['naming_issues'])}个")
    
    if report['thin_files']:
        print("\n偏薄文件:")
        for f in report['thin_files']:
            print(f"  {f['size_kb']}KB  {f['dir']}/{f['file']}")
    
    if report['empty_dirs']:
        print("\n空目录:")
        for d in report['empty_dirs']:
            print(f"  {d}")
    
    if report['naming_issues']:
        print("\n编号问题:")
        for n in report['naming_issues']:
            print(f"  {n}")
    
    # 写入JSON供cron job读取
    json_path = os.path.join(BASE, "计划", "scan_result.json")
    with open(json_path, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 有问题返回1
    if report['thin_files'] or report['empty_dirs'] or report['naming_issues']:
        sys.exit(1)
    else:
        print("\n✅ 知识库健康度良好")
        sys.exit(0)
