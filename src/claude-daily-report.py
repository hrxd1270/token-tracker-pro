#!/usr/bin/env python3
"""
Claude Code 日报生成器
生成昨日使用情况和累计统计
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "token-usage-pro.json"

def parse_iso(dt_string):
    """解析 ISO 格式时间字符串"""
    dt_string = dt_string.replace('Z', '+00:00')
    if '+' in dt_string:
        dt_string = dt_string.split('+')[0]
    if '.' in dt_string:
        return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")

def load_data():
    """加载数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"records": [], "total": {"in": 0, "out": 0, "calls": 0, "success": 0, "failed": 0}}

def generate_report():
    """生成日报"""
    data = load_data()
    
    if not data["records"]:
        return "📊 今日暂无 Claude Code 使用记录～"
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 筛选昨天的记录
    yesterday_records = [
        r for r in data["records"]
        if yesterday_start <= parse_iso(r["timestamp"]) <= yesterday_end
    ]
    
    # 计算昨日统计
    yesterday_in = sum(r["tokens_in"] for r in yesterday_records)
    yesterday_out = sum(r["tokens_out"] for r in yesterday_records)
    yesterday_calls = len(yesterday_records)
    yesterday_success = sum(1 for r in yesterday_records if r.get("success", True))
    yesterday_failed = yesterday_calls - yesterday_success
    
    # 性能指标
    ttft_records = [r for r in yesterday_records if r.get("ttft")]
    rate_records = [r for r in yesterday_records if r.get("token_rate")]
    avg_ttft = sum(r["ttft"] for r in ttft_records) / len(ttft_records) if ttft_records else None
    avg_rate = sum(r["token_rate"] for r in rate_records) / len(rate_records) if rate_records else None
    
    # 累计统计
    total_in = data["total"]["in"]
    total_out = data["total"]["out"]
    total_calls = data["total"]["calls"]
    total_success = data["total"].get("success", 0)
    total_failed = data["total"].get("failed", 0)
    
    # 按模型统计（昨日）
    model_stats = {}
    for r in yesterday_records:
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
    
    # 按任务统计（昨日）
    task_stats = {}
    for r in yesterday_records:
        task = r.get("task", "未知")[:20]
        if task not in task_stats:
            task_stats[task] = {"in": 0, "out": 0, "calls": 0}
        task_stats[task]["in"] += r["tokens_in"]
        task_stats[task]["out"] += r["tokens_out"]
        task_stats[task]["calls"] += 1
    
    # 生成报告
    report = []
    report.append(f"📊 Claude Code 使用日报 ({yesterday.strftime('%m-%d')})")
    report.append("=" * 60)
    
    if yesterday_calls == 0:
        report.append("😴 昨日暂无使用记录～")
    else:
        success_rate = (yesterday_success / yesterday_calls * 100) if yesterday_calls > 0 else 0
        report.append(f"📞 调用次数：{yesterday_calls}")
        report.append(f"✅ 成功：{yesterday_success} | ❌ 失败：{yesterday_failed} | 成功率：{success_rate:.0f}%")
        report.append(f"📥 输入：{yesterday_in:,} tokens")
        report.append(f"📤 输出：{yesterday_out:,} tokens")
        report.append(f"📈 总计：{yesterday_in + yesterday_out:,} tokens")
        
        if avg_ttft or avg_rate:
            report.append("")
            report.append("⚡ 性能指标:")
            if avg_ttft:
                report.append(f"  首 token 耗时：{avg_ttft:.2f}s")
            if avg_rate:
                report.append(f"  平均速率：{avg_rate:.0f} tokens/s")
        
        if task_stats:
            report.append("")
            report.append("📁 任务统计:")
            for task, stats in sorted(task_stats.items(), key=lambda x: x[1]["calls"], reverse=True)[:5]:
                report.append(f"  • {task}: {stats['calls']} 次 | {stats['in'] + stats['out']:,} tokens")
    
    report.append("")
    report.append("=" * 60)
    report.append("📈 累计统计:")
    total_success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0
    report.append(f"  总调用：{total_calls} 次 | 成功率：{total_success_rate:.0f}%")
    report.append(f"  总消耗：{total_in + total_out:,} tokens")
    report.append(f"  (输入：{total_in:,} / 输出：{total_out:,})")
    
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())
