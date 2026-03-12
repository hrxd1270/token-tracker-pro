#!/usr/bin/env python3
"""
增强版 Token 使用记录工具 - 支持详细性能指标
用法:
    python3 token-tracker-pro.py log --in 1000 --out 500 --model claude-sonnet-4-5-20250929 --task "代码审查" --ttft 1.5 --success true --duration 10.5
    python3 token-tracker-pro.py stats
    python3 token-tracker-pro.py history --days 7
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "token-usage-pro.json"

def load_data():
    """加载数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"records": [], "total": {"in": 0, "out": 0, "calls": 0, "success": 0, "failed": 0}}

def save_data(data):
    """保存数据"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_usage(tokens_in, tokens_out, model="unknown", task="unknown", 
              ttft=None, duration=None, success=True, token_rate=None,
              error_msg=None):
    """记录一次 token 使用（增强版）"""
    data = load_data()
    
    # 计算 token 速率（tokens/秒）
    if token_rate is None and duration and duration > 0:
        token_rate = (tokens_in + tokens_out) / duration
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_total": tokens_in + tokens_out,
        "model": model,
        "task": task,
        "ttft": ttft,  # 首 token 耗时 (秒)
        "duration": duration,  # 总耗时 (秒)
        "token_rate": round(token_rate, 2) if token_rate else None,  # tokens/秒
        "success": success,
        "error_msg": error_msg
    }
    
    data["records"].append(record)
    data["total"]["in"] += tokens_in
    data["total"]["out"] += tokens_out
    data["total"]["calls"] += 1
    if success:
        data["total"]["success"] += 1
    else:
        data["total"]["failed"] += 1
    
    save_data(data)
    
    status = "✅" if success else "❌"
    print(f"{status} 已记录：输入={tokens_in}, 输出={tokens_out}, 总计={tokens_in + tokens_out}")
    if ttft:
        print(f"   首 token: {ttft:.2f}s | 总耗时：{duration:.2f}s | 速率：{token_rate:.0f} tokens/s")
    return record

def show_stats(days=None):
    """显示统计信息"""
    data = load_data()
    
    if not data["records"]:
        print("📊 暂无使用记录")
        return
    
    now = datetime.now()
    records = data["records"]
    
    if days:
        cutoff = now - timedelta(days=days)
        records = [r for r in records if parse_iso(r["timestamp"]) >= cutoff]
    
    if not records:
        print(f"📊 过去 {days} 天暂无使用记录")
        return
    
    # 统计数据
    total_in = sum(r["tokens_in"] for r in records)
    total_out = sum(r["tokens_out"] for r in records)
    total_calls = len(records)
    success_calls = sum(1 for r in records if r.get("success", True))
    failed_calls = total_calls - success_calls
    success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0
    
    # 性能统计
    ttft_records = [r for r in records if r.get("ttft")]
    duration_records = [r for r in records if r.get("duration")]
    rate_records = [r for r in records if r.get("token_rate")]
    
    avg_ttft = sum(r["ttft"] for r in ttft_records) / len(ttft_records) if ttft_records else None
    avg_duration = sum(r["duration"] for r in duration_records) / len(duration_records) if duration_records else None
    avg_rate = sum(r["token_rate"] for r in rate_records) / len(rate_records) if rate_records else None
    
    # 按模型统计
    model_stats = {}
    for r in records:
        model = r["model"]
        if model not in model_stats:
            model_stats[model] = {"in": 0, "out": 0, "calls": 0, "success": 0, "failed": 0}
        model_stats[model]["in"] += r["tokens_in"]
        model_stats[model]["out"] += r["tokens_out"]
        model_stats[model]["calls"] += 1
        if r.get("success", True):
            model_stats[model]["success"] += 1
        else:
            model_stats[model]["failed"] += 1
    
    # 输出
    time_range = f"过去 {days} 天" if days else "全部时间"
    print(f"\n📊 Token 使用统计 ({time_range})")
    print("=" * 60)
    print(f"📞 调用次数：{total_calls}")
    print(f"✅ 成功：{success_calls} | ❌ 失败：{failed_calls} | 成功率：{success_rate:.1f}%")
    print(f"📥 总输入：{total_in:,} tokens")
    print(f"📤 总输出：{total_out:,} tokens")
    print(f"📈 总计：{total_in + total_out:,} tokens")
    print(f"📉 平均每次：输入={total_in/total_calls:.0f}, 输出={total_out/total_calls:.0f}")
    
    if avg_ttft or avg_duration or avg_rate:
        print(f"\n⚡ 性能指标:")
        print("-" * 60)
        if avg_ttft:
            print(f"  首 token 耗时 (TTFT): {avg_ttft:.2f}s")
        if avg_duration:
            print(f"  平均请求耗时：{avg_duration:.2f}s")
        if avg_rate:
            print(f"  平均 token 速率：{avg_rate:.0f} tokens/s")
    
    if model_stats:
        print(f"\n📚 按模型统计:")
        print("-" * 60)
        for model, stats in sorted(model_stats.items(), key=lambda x: x[1]["calls"], reverse=True):
            print(f"  {model}:")
            print(f"    调用：{stats['calls']} 次 | 成功：{stats['success']} | 失败：{stats['failed']}")
            print(f"    输入：{stats['in']:,} | 输出：{stats['out']:,} | 总计：{stats['in'] + stats['out']:,}")
    
    print()

def show_history(days=7, limit=20):
    """显示最近的使用记录"""
    data = load_data()
    
    if not data["records"]:
        print("📜 暂无使用记录")
        return
    
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    records = [r for r in data["records"] if parse_iso(r["timestamp"]) >= cutoff]
    
    if not records:
        print(f"📜 过去 {days} 天暂无使用记录")
        return
    
    records = sorted(records, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    print(f"\n📜 最近使用记录 (过去 {days} 天，最多 {limit} 条)")
    print("=" * 80)
    
    for r in records:
        ts = parse_iso(r["timestamp"]).strftime("%m-%d %H:%M")
        status = "✅" if r.get("success", True) else "❌"
        perf = ""
        if r.get("ttft"):
            perf = f"| TTFT:{r['ttft']:.1f}s"
        if r.get("token_rate"):
            perf += f" | {r['token_rate']:.0f}t/s"
        print(f"{ts} {status} | {r['model'][:20]:<20} | 入:{r['tokens_in']:>6} 出:{r['tokens_out']:>6} {perf} | {r.get('task', 'N/A')[:15]}")
    
    print()

def parse_iso(dt_string):
    """解析 ISO 格式时间字符串"""
    dt_string = dt_string.replace('Z', '+00:00')
    if '+' in dt_string:
        dt_string = dt_string.split('+')[0]
    if '.' in dt_string:
        return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")

def reset():
    """清空记录"""
    confirm = input("⚠️  确定要清空所有记录吗？(y/N): ")
    if confirm.lower() == 'y':
        save_data({"records": [], "total": {"in": 0, "out": 0, "calls": 0, "success": 0, "failed": 0}})
        print("✅ 已清空所有记录")
    else:
        print("❌ 已取消")

def main():
    parser = argparse.ArgumentParser(description="Token 使用记录工具 (增强版)")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # log 命令
    log_parser = subparsers.add_parser("log", help="记录一次 token 使用")
    log_parser.add_argument("--in", dest="tokens_in", type=int, required=True, help="输入 token 数")
    log_parser.add_argument("--out", dest="tokens_out", type=int, required=True, help="输出 token 数")
    log_parser.add_argument("--model", type=str, default="unknown", help="模型名称")
    log_parser.add_argument("--task", type=str, default="unknown", help="任务描述")
    log_parser.add_argument("--ttft", type=float, help="首 token 耗时 (秒)")
    log_parser.add_argument("--duration", type=float, help="总耗时 (秒)")
    log_parser.add_argument("--rate", dest="token_rate", type=float, help="Token 速率 (tokens/秒)")
    log_parser.add_argument("--success", type=str, default="true", help="是否成功 (true/false)")
    log_parser.add_argument("--error", dest="error_msg", type=str, help="错误信息")
    
    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    stats_parser.add_argument("--days", type=int, help="统计最近 N 天")
    
    # history 命令
    history_parser = subparsers.add_parser("history", help="显示使用历史")
    history_parser.add_argument("--days", type=int, default=7, help="显示最近 N 天")
    history_parser.add_argument("--limit", type=int, default=20, help="最多显示条数")
    
    # reset 命令
    subparsers.add_parser("reset", help="清空记录")
    
    args = parser.parse_args()
    
    if args.command == "log":
        success = args.success.lower() in ("true", "1", "yes")
        log_usage(
            args.tokens_in, args.tokens_out,
            model=args.model, task=args.task,
            ttft=args.ttft, duration=args.duration,
            token_rate=args.token_rate, success=success,
            error_msg=args.error_msg
        )
    elif args.command == "stats":
        show_stats(args.days)
    elif args.command == "history":
        show_history(args.days, args.limit)
    elif args.command == "reset":
        reset()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
