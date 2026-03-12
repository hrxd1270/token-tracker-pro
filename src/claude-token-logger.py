#!/usr/bin/env python3
"""
Claude Code Token 日志解析器
解析 Claude Code 的输出日志，提取 token 使用、耗时等指标

用法:
    # 方式 1: 管道方式
    claude < prompt.txt | python3 claude-token-logger.py --task "代码审查"
    
    # 方式 2: 日志文件方式
    python3 claude-token-logger.py --log claude-output.log --task "代码审查"
    
    # 方式 3: 手动输入
    python3 claude-token-logger.py --in 5000 --out 1000 --ttft 1.5 --duration 10.5 --task "代码审查"
"""

import json
import re
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

TRACKER = Path.home() / ".openclaw" / "workspace" / "scripts" / "token-tracker-pro.py"

def parse_claude_output(output):
    """解析 Claude Code 的输出，提取指标"""
    metrics = {
        "tokens_in": 0,
        "tokens_out": 0,
        "ttft": None,
        "duration": None,
        "success": True,
        "error_msg": None
    }
    
    # 匹配 token 使用
    # 示例：Tokens: 5.2k input, 1.2k output
    token_pattern = r'Tokens:\s*([\d.]+[kM]?)\s*input,\s*([\d.]+[kM]?)\s*output'
    match = re.search(token_pattern, output, re.IGNORECASE)
    if match:
        metrics["tokens_in"] = parse_token_count(match.group(1))
        metrics["tokens_out"] = parse_token_count(match.group(2))
    
    # 匹配耗时
    # 示例：Duration: 10.5s
    duration_pattern = r'Duration:\s*([\d.]+)s'
    match = re.search(duration_pattern, output, re.IGNORECASE)
    if match:
        metrics["duration"] = float(match.group(1))
    
    # 匹配首 token 时间
    # 示例：Time to first token: 1.5s
    ttft_pattern = r'Time to first token:\s*([\d.]+)s'
    match = re.search(ttft_pattern, output, re.IGNORECASE)
    if match:
        metrics["ttft"] = float(match.group(1))
    
    # 检测错误
    if "error" in output.lower() or "failed" in output.lower():
        # 尝试提取错误信息
        error_pattern = r'(?:error|failed):\s*(.+?)(?:\n|$)'
        match = re.search(error_pattern, output, re.IGNORECASE)
        if match:
            metrics["error_msg"] = match.group(1).strip()[:200]
            metrics["success"] = False
    
    # 计算 token 速率
    if metrics["duration"] and metrics["duration"] > 0:
        metrics["token_rate"] = (metrics["tokens_in"] + metrics["tokens_out"]) / metrics["duration"]
    else:
        metrics["token_rate"] = None
    
    return metrics

def parse_token_count(token_str):
    """解析 token 数量（支持 k/M 后缀）"""
    token_str = token_str.lower().strip()
    if token_str.endswith('k'):
        return int(float(token_str[:-1]) * 1000)
    elif token_str.endswith('m'):
        return int(float(token_str[:-1]) * 1000000)
    else:
        return int(float(token_str))

def log_to_tracker(metrics, model, task):
    """记录到 tracker"""
    cmd = [
        "python3", str(TRACKER),
        "log",
        "--in", str(metrics["tokens_in"]),
        "--out", str(metrics["tokens_out"]),
        "--model", model,
        "--task", task
    ]
    
    if metrics["ttft"]:
        cmd.extend(["--ttft", str(metrics["ttft"])])
    if metrics["duration"]:
        cmd.extend(["--duration", str(metrics["duration"])])
    if metrics["token_rate"]:
        cmd.extend(["--rate", str(metrics["token_rate"])])
    
    cmd.extend(["--success", str(metrics["success"]).lower()])
    if metrics["error_msg"]:
        cmd.extend(["--error", metrics["error_msg"]])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

def main():
    parser = argparse.ArgumentParser(description="Claude Code Token 日志解析器")
    parser.add_argument("--log", type=str, help="日志文件路径")
    parser.add_argument("--task", type=str, default="Claude Code", help="任务描述")
    parser.add_argument("--model", type=str, default="claude-code", help="模型名称")
    parser.add_argument("--in", dest="tokens_in", type=int, help="手动输入 token 数")
    parser.add_argument("--out", dest="tokens_out", type=int, help="手动输出 token 数")
    parser.add_argument("--ttft", type=float, help="首 token 耗时 (秒)")
    parser.add_argument("--duration", type=float, help="总耗时 (秒)")
    parser.add_argument("--rate", dest="token_rate", type=float, help="Token 速率")
    
    args = parser.parse_args()
    
    metrics = {
        "tokens_in": args.tokens_in or 0,
        "tokens_out": args.tokens_out or 0,
        "ttft": args.ttft,
        "duration": args.duration,
        "token_rate": args.token_rate,
        "success": True,
        "error_msg": None
    }
    
    if args.log:
        # 从日志文件解析
        with open(args.log, 'r', encoding='utf-8') as f:
            output = f.read()
        parsed = parse_claude_output(output)
        metrics.update(parsed)
        print(f"📄 从日志文件解析：{args.log}")
    else:
        # 从 stdin 读取
        if not sys.stdin.isatty():
            output = sys.stdin.read()
            if output.strip():
                parsed = parse_claude_output(output)
                metrics.update(parsed)
                print("📄 从 stdin 解析输出")
    
    print(f"\n📊 提取的指标:")
    print(f"  输入：{metrics['tokens_in']:,} tokens")
    print(f"  输出：{metrics['tokens_out']:,} tokens")
    if metrics["ttft"]:
        print(f"  首 token: {metrics['ttft']:.2f}s")
    if metrics["duration"]:
        print(f"  总耗时：{metrics['duration']:.2f}s")
    if metrics["token_rate"]:
        print(f"  速率：{metrics['token_rate']:.0f} tokens/s")
    print(f"  状态：{'✅ 成功' if metrics['success'] else '❌ 失败'}")
    
    log_to_tracker(metrics, args.model, args.task)

if __name__ == "__main__":
    main()
