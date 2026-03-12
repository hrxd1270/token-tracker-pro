#!/usr/bin/env python3
"""
Claude Code 历史日志导入工具
自动查找并解析 Claude Code 的历史日志文件，导入到 token 统计系统

用法:
    python3 claude-history-import.py              # 自动查找并导入
    python3 claude-history-import.py --dir ~/logs # 指定日志目录
    python3 claude-history-import.py --dry-run    # 预览模式
"""

import json
import re
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 支持多种日志格式
LOG_PATTERNS = [
    # Claude Code CLI 输出格式
    r'Tokens:\s*([\d.]+[kM]?)\s*input,\s*([\d.]+[kM]?)\s*output',
    r'Usage:\s*([\d.]+[kM]?)\s*input,\s*([\d.]+[kM]?)\s*output',
    
    # Anthropic API 格式
    r'"input_tokens":\s*(\d+).*?"output_tokens":\s*(\d+)',
    r'"prompt_tokens":\s*(\d+).*?"completion_tokens":\s*(\d+)',
    
    # 其他常见格式
    r'prompt_tokens[=:]\s*(\d+).*?completion_tokens[=:]\s*(\d+)',
]

DURATION_PATTERNS = [
    r'Duration:\s*([\d.]+)s',
    r'Total time:\s*([\d.]+)s',
    r'Elapsed:\s*([\d.]+)s',
    r'Time taken:\s*([\d.]+)s',
]

TTFT_PATTERNS = [
    r'Time to first token:\s*([\d.]+)s',
    r'TTFT:\s*([\d.]+)s',
    r'First token:\s*([\d.]+)s',
]

def parse_token_count(token_str):
    """解析 token 数量（支持 k/M 后缀）"""
    token_str = str(token_str).lower().strip()
    try:
        if token_str.endswith('k'):
            return int(float(token_str[:-1]) * 1000)
        elif token_str.endswith('m'):
            return int(float(token_str[:-1]) * 1000000)
        else:
            return int(float(token_str))
    except:
        return 0

def parse_log_file(file_path):
    """解析单个日志文件"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  读取失败 {file_path}: {e}")
        return None
    
    records = []
    
    # 尝试匹配 token 使用
    tokens_in = 0
    tokens_out = 0
    duration = None
    ttft = None
    
    for pattern in LOG_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            tokens_in = parse_token_count(match.group(1))
            tokens_out = parse_token_count(match.group(2))
            break
    
    # 匹配耗时
    for pattern in DURATION_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            duration = float(match.group(1))
            break
    
    # 匹配首 token 时间
    for pattern in TTFT_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            ttft = float(match.group(1))
            break
    
    # 如果找到 token 数据，创建记录
    if tokens_in > 0 or tokens_out > 0:
        # 获取文件修改时间
        try:
            mtime = os.path.getmtime(file_path)
            timestamp = datetime.fromtimestamp(mtime).isoformat()
        except:
            timestamp = datetime.now().isoformat()
        
        # 尝试从文件名或内容提取任务描述
        task = extract_task(file_path, content)
        
        records.append({
            "timestamp": timestamp,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_total": tokens_in + tokens_out,
            "model": "claude-code",
            "task": task,
            "duration": duration,
            "ttft": ttft,
            "success": True,
            "source_file": str(file_path)
        })
    
    return records

def extract_task(file_path, content):
    """从日志中提取任务描述"""
    # 尝试从文件名提取
    filename = os.path.basename(file_path)
    
    # 尝试从内容第一行提取（通常是 prompt）
    lines = content.strip().split('\n')
    if lines:
        first_line = lines[0][:50].strip()
        if first_line and len(first_line) > 5:
            return first_line
    
    return filename

def find_log_files(search_dirs=None):
    """查找可能的日志文件"""
    if search_dirs is None:
        # 默认搜索目录
        search_dirs = [
            Path.home() / ".claude",
            Path.home() / ".config" / "Claude",
            Path.home() / "Library" / "Logs" / "Claude",
            Path.home() / "Library" / "Application Support" / "Claude",
            Path.home() / ".local" / "share" / "Claude",
            Path.cwd(),  # 当前目录
        ]
    
    log_files = []
    
    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        
        # 查找 .log 文件
        for log_file in base_dir.rglob("*.log"):
            log_files.append(log_file)
        
        # 查找 .json 文件（可能是 API 响应）
        for json_file in base_dir.rglob("*.json"):
            log_files.append(json_file)
        
        # 查找 .txt 文件
        for txt_file in base_dir.rglob("*.txt"):
            log_files.append(txt_file)
    
    # 去重
    return list(set(log_files))

def import_to_tracker(record, tracker_path, dry_run=False):
    """导入单个记录到 tracker"""
    if dry_run:
        return True
    
    cmd = [
        "python3", str(tracker_path),
        "log",
        "--in", str(record["tokens_in"]),
        "--out", str(record["tokens_out"]),
        "--model", record["model"],
        "--task", record["task"],
        "--success", "true"
    ]
    
    if record.get("ttft"):
        cmd.extend(["--ttft", str(record["ttft"])])
    if record.get("duration"):
        cmd.extend(["--duration", str(record["duration"])])
    
    import subprocess
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Claude Code 历史日志导入工具")
    parser.add_argument("--dir", "-d", type=str, action="append", help="指定日志目录（可多次）")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际导入")
    parser.add_argument("--days", type=int, help="只导入最近 N 天的日志")
    parser.add_argument("--tracker", type=str, help="token-tracker-pro.py 路径")
    
    args = parser.parse_args()
    
    # 确定 tracker 路径
    if args.tracker:
        tracker_path = Path(args.tracker)
    else:
        # 默认路径
        tracker_path = Path(__file__).parent / "token-tracker-pro.py"
        if not tracker_path.exists():
            tracker_path = Path.home() / ".openclaw" / "workspace" / "token-tracker" / "src" / "token-tracker-pro.py"
    
    if not tracker_path.exists():
        print(f"❌ 找不到 token-tracker-pro.py: {tracker_path}")
        return
    
    print("🔍 搜索日志文件...")
    
    # 搜索目录
    search_dirs = [Path(d) for d in args.dir] if args.dir else None
    log_files = find_log_files(search_dirs)
    
    if not log_files:
        print("❌ 未找到日志文件")
        print("\n💡 提示：")
        print("  - 使用 --dir 指定日志目录")
        print("  - 常见位置：~/.claude/, ~/Library/Logs/Claude/, ~/.config/Claude/")
        return
    
    print(f"📁 找到 {len(log_files)} 个可能的日志文件")
    
    # 解析日志
    print("\n📄 解析日志文件...")
    all_records = []
    
    for log_file in log_files:
        records = parse_log_file(log_file)
        if records:
            all_records.extend(records)
            if not args.dry_run:
                print(f"  ✅ {log_file} - {len(records)} 条记录")
    
    if not all_records:
        print("\n❌ 未在日志中找到 token 使用记录")
        print("\n💡 提示：")
        print("  - 检查日志格式是否匹配")
        print("  - 使用 --dry-run 查看解析结果")
        return
    
    print(f"\n📊 共解析 {len(all_records)} 条记录")
    
    # 按时间筛选
    if args.days:
        cutoff = datetime.now() - timedelta(days=args.days)
        all_records = [
            r for r in all_records
            if datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]
        print(f"📅 最近 {args.days} 天：{len(all_records)} 条记录")
    
    if args.dry_run:
        print("\n📋 预览导入内容:")
        print("=" * 80)
        for record in sorted(all_records, key=lambda x: x["timestamp"], reverse=True)[:20]:
            dt = record["timestamp"][:16].replace('T', ' ')
            print(f"{dt} | {record['model']:<15} | 入:{record['tokens_in']:>7} 出:{record['tokens_out']:>6} | {record['task'][:30]}")
        return
    
    # 导入到 tracker
    print(f"\n🚀 开始导入到 token tracker...")
    success_count = 0
    
    for record in all_records:
        if import_to_tracker(record, tracker_path, args.dry_run):
            success_count += 1
    
    print(f"\n✅ 导入完成！成功导入 {success_count}/{len(all_records)} 条记录")
    print(f"\n📊 查看统计:")
    print(f"  python3 {tracker_path} stats")
    print(f"  python3 {tracker_path} history --days 30")

if __name__ == "__main__":
    from datetime import timedelta
    main()
