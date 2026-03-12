#!/usr/bin/env python3
"""
Claude Code 包装器 - 自动记录 token 使用并生成报告
用法:
    python3 claude-wrapper.py "帮我写个函数"
    python3 claude-wrapper.py --file script.py "优化这个脚本"
    python3 claude-wrapper.py --stats  # 查看统计
"""

import subprocess
import sys
import argparse
import json
import re
import os
from datetime import datetime
from pathlib import Path

TRACKER = Path.home() / ".openclaw" / "workspace" / "scripts" / "token-tracker-pro.py"
LOG_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "claude-logs"

def parse_claude_metrics(output):
    """从 Claude Code 输出中提取指标"""
    metrics = {
        "tokens_in": 0,
        "tokens_out": 0,
        "ttft": None,
        "duration": None,
        "success": True,
        "error_msg": None
    }
    
    # 匹配 token 使用（多种格式）
    patterns = [
        r'Tokens:\s*([\d.]+[kM]?)\s*input,\s*([\d.]+[kM]?)\s*output',
        r'Usage:\s*([\d.]+[kM]?)\s*input,\s*([\d.]+[kM]?)\s*output',
        r'Input tokens:\s*([\d.]+[kM]?).*?Output tokens:\s*([\d.]+[kM]?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            metrics["tokens_in"] = parse_token_count(match.group(1))
            metrics["tokens_out"] = parse_token_count(match.group(2))
            break
    
    # 匹配耗时
    duration_patterns = [
        r'Duration:\s*([\d.]+)s',
        r'Total time:\s*([\d.]+)s',
        r'Elapsed:\s*([\d.]+)s',
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            metrics["duration"] = float(match.group(1))
            break
    
    # 匹配首 token 时间
    ttft_patterns = [
        r'Time to first token:\s*([\d.]+)s',
        r'TTFT:\s*([\d.]+)s',
        r'First token:\s*([\d.]+)s',
    ]
    
    for pattern in ttft_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            metrics["ttft"] = float(match.group(1))
            break
    
    # 检测错误
    if "error" in output.lower() or "failed" in output.lower() or "Error:" in output:
        error_patterns = [
            r'(?:error|Error):\s*(.+?)(?:\n|$)',
            r'Failed to (.+?)(?:\n|$)',
        ]
        for pattern in error_patterns:
            match = re.search(pattern, output)
            if match:
                metrics["error_msg"] = match.group(1).strip()[:200]
                metrics["success"] = False
                break
    
    # 计算 token 速率
    if metrics["duration"] and metrics["duration"] > 0:
        total_tokens = metrics["tokens_in"] + metrics["tokens_out"]
        if total_tokens > 0:
            metrics["token_rate"] = total_tokens / metrics["duration"]
    
    return metrics

def parse_token_count(token_str):
    """解析 token 数量"""
    token_str = token_str.lower().strip()
    try:
        if token_str.endswith('k'):
            return int(float(token_str[:-1]) * 1000)
        elif token_str.endswith('m'):
            return int(float(token_str[:-1]) * 1000000)
        else:
            return int(float(token_str))
    except:
        return 0

def log_usage(metrics, model, task):
    """记录到 tracker"""
    cmd = [
        "python3", str(TRACKER),
        "log",
        "--in", str(metrics["tokens_in"]),
        "--out", str(metrics["tokens_out"]),
        "--model", model,
        "--task", task,
        "--success", str(metrics["success"]).lower()
    ]
    
    if metrics["ttft"]:
        cmd.extend(["--ttft", str(metrics["ttft"])])
    if metrics["duration"]:
        cmd.extend(["--duration", str(metrics["duration"])])
    if metrics.get("token_rate"):
        cmd.extend(["--rate", str(metrics["token_rate"])])
    if metrics["error_msg"]:
        cmd.extend(["--error", metrics["error_msg"]])
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.stdout

def show_stats(days=1):
    """显示统计"""
    cmd = ["python3", str(TRACKER), "stats", "--days", str(days)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

def show_history(limit=5):
    """显示最近历史"""
    cmd = ["python3", str(TRACKER), "history", "--limit", str(limit)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

def generate_report(metrics, task, duration_str):
    """生成报告"""
    report = []
    report.append("\n" + "=" * 60)
    report.append("📊 Claude Code 执行报告")
    report.append("=" * 60)
    report.append(f"任务：{task}")
    report.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"耗时：{duration_str}")
    report.append("")
    
    if metrics["tokens_in"] > 0 or metrics["tokens_out"] > 0:
        report.append("📈 Token 使用:")
        report.append(f"  输入：{metrics['tokens_in']:,} tokens")
        report.append(f"  输出：{metrics['tokens_out']:,} tokens")
        report.append(f"  总计：{metrics['tokens_in'] + metrics['tokens_out']:,} tokens")
    
    if metrics["ttft"]:
        report.append(f"\n⚡ 性能:")
        report.append(f"  首 token 耗时：{metrics['ttft']:.2f}s")
    if metrics.get("token_rate"):
        report.append(f"  Token 速率：{metrics['token_rate']:.0f} tokens/s")
    
    if metrics["success"]:
        report.append(f"\n✅ 状态：成功")
    else:
        report.append(f"\n❌ 状态：失败")
        if metrics["error_msg"]:
            report.append(f"错误：{metrics['error_msg']}")
    
    report.append("=" * 60)
    
    return "\n".join(report)

def run_claude(args, task, model):
    """运行 Claude Code"""
    # 构建命令
    cmd = ["claude"] + args
    
    print(f"🚀 执行 Claude Code: {' '.join(cmd)}")
    print("-" * 60)
    
    # 执行并捕获输出
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=300  # 5 分钟超时
        )
        
        output = result.stdout + result.stderr
        
        # 打印原始输出
        print(output)
        
        # 解析指标
        metrics = parse_claude_metrics(output)
        
        # 如果没有自动检测到指标，尝试估算
        if metrics["tokens_in"] == 0 and metrics["tokens_out"] == 0:
            # 简单估算：输入长度 / 4 + 输出长度 / 4
            input_len = len(' '.join(args))
            output_len = len(output)
            metrics["tokens_in"] = input_len // 4
            metrics["tokens_out"] = output_len // 4
        
        # 记录使用
        log_output = log_usage(metrics, model, task)
        
        # 生成报告
        report = generate_report(metrics, task, f"{result.returncode}")
        print(report)
        
        # 显示统计摘要
        print("\n📊 累计统计 (过去 7 天):")
        show_stats(7)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("❌ 执行超时（>5 分钟）")
        return 1
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Claude Code 包装器 - 自动记录 token 使用")
    parser.add_argument("prompt", nargs="?", help="提示词")
    parser.add_argument("--file", "-f", type=str, help="输入文件")
    parser.add_argument("--model", "-m", type=str, default="claude-sonnet-4-5-20250929", help="模型")
    parser.add_argument("--task", "-t", type=str, help="任务描述（默认使用 prompt 前 20 字）")
    parser.add_argument("--stats", "-s", action="store_true", help="查看统计")
    parser.add_argument("--history", action="store_true", help="查看历史")
    
    args = parser.parse_args()
    
    # 查看统计
    if args.stats:
        show_stats(7)
        return
    
    # 查看历史
    if args.history:
        show_history(10)
        return
    
    # 检查 prompt
    if not args.prompt and not args.file:
        parser.print_help()
        print("\n❌ 请提供 prompt 或文件")
        return
    
    # 构建 claude 参数
    claude_args = []
    task = args.task or (args.prompt[:20] if args.prompt else "文件处理")
    
    if args.file:
        claude_args.extend(["--file", args.file])
        task = f"文件：{args.file}"
    
    if args.prompt:
        claude_args.append(args.prompt)
    
    # 运行
    sys.exit(run_claude(claude_args, task, args.model))

if __name__ == "__main__":
    main()
