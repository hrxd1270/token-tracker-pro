#!/usr/bin/env python3
"""
OpenClaw Session 历史导入工具
从 OpenClaw 的 session 存储中解析历史 token 使用记录

用法:
    python3 openclaw-session-import.py              # 导入所有会话
    python3 openclaw-session-import.py --days 7     # 只导入最近 7 天
    python3 openclaw-session-import.py --dry-run    # 预览不导入
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

TRACKER = Path.home() / ".openclaw" / "workspace" / "token-tracker" / "src" / "token-tracker-pro.py"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "session-import-state.json"

def parse_iso(dt_string):
    """解析 ISO 格式时间字符串"""
    dt_string = dt_string.replace('Z', '+00:00')
    if '+' in dt_string:
        dt_string = dt_string.split('+')[0]
    if '.' in dt_string:
        return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")

def load_state():
    """加载已导入的会话状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"imported_sessions": [], "last_import": None}

def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_sessions():
    """获取所有会话"""
    result = subprocess.run(
        ["openclaw", "sessions", "--json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if result.returncode != 0:
        print(f"❌ 获取会话失败：{result.stderr}")
        return []
    
    try:
        data = json.loads(result.stdout)
        return data.get("sessions", [])
    except json.JSONDecodeError:
        print(f"❌ 解析 JSON 失败：{result.stdout}")
        return []

def import_session(session, dry_run=False):
    """导入单个会话的 token 记录"""
    key = session.get("key", "")
    tokens_in = session.get("inputTokens", 0)
    tokens_out = session.get("outputTokens", 0)
    model = session.get("model", "unknown")
    kind = session.get("kind", "unknown")
    updated_at = session.get("updatedAt", 0)
    
    if tokens_in == 0 and tokens_out == 0:
        return None
    
    # 转换时间戳
    if updated_at:
        dt = datetime.fromtimestamp(updated_at / 1000)
        timestamp = dt.isoformat()
    else:
        dt = datetime.now()
        timestamp = dt.isoformat()
    
    # 提取任务类型
    if "cron:" in key:
        # 尝试从 cron ID 提取任务名
        if "11ea49ff" in key:
            task = "每日笑话推送"
        elif "0d772d9d" in key:
            task = "Token 使用日报"
        elif "474c35ea" in key:
            task = "Claude Code 日报"
        else:
            task = "cron 任务"
    elif "qqbot:" in key:
        task = "QQ 对话"
    else:
        task = kind
    
    if dry_run:
        return {
            "timestamp": timestamp,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model": model,
            "task": task,
            "key": key
        }
    
    # 记录到 tracker
    cmd = [
        "python3", str(TRACKER),
        "log",
        "--in", str(tokens_in),
        "--out", str(tokens_out),
        "--model", model,
        "--task", f"{task} ({key[:30]})"
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Session 历史导入工具")
    parser.add_argument("--days", type=int, help="只导入最近 N 天的会话")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际导入")
    parser.add_argument("--reset", action="store_true", help="重置导入状态")
    
    args = parser.parse_args()
    
    if args.reset:
        save_state({"imported_sessions": [], "last_import": None})
        print("✅ 已重置导入状态")
        return
    
    print("📊 获取会话列表...")
    sessions = get_sessions()
    
    if not sessions:
        print("❌ 没有会话记录")
        return
    
    print(f"📈 发现 {len(sessions)} 个会话")
    
    # 加载已导入状态
    state = load_state()
    imported = set(state.get("imported_sessions", []))
    
    # 筛选未导入的会话
    now = datetime.now()
    new_sessions = []
    
    for session in sessions:
        key = session.get("key", "")
        
        # 跳过已导入的
        if key in imported:
            continue
        
        # 按时间筛选
        if args.days:
            updated_at = session.get("updatedAt", 0)
            if updated_at:
                dt = datetime.fromtimestamp(updated_at / 1000)
                if dt < now - timedelta(days=args.days):
                    continue
        
        new_sessions.append(session)
    
    if not new_sessions:
        print("✅ 没有需要导入的新会话")
        return
    
    print(f"📥 待导入：{len(new_sessions)} 个会话")
    
    if args.dry_run:
        print("\n📋 预览导入内容:")
        print("=" * 80)
        for session in new_sessions:
            preview = import_session(session, dry_run=True)
            if preview:
                dt = preview["timestamp"][:16].replace('T', ' ')
                print(f"{dt} | {preview['model'][:20]:<20} | 入:{preview['tokens_in']:>7} 出:{preview['tokens_out']:>6} | {preview['task'][:25]}")
        return
    
    # 开始导入
    print("\n🚀 开始导入...")
    success_count = 0
    
    for session in new_sessions:
        key = session.get("key", "")
        result = import_session(session)
        
        if result:
            imported.add(key)
            success_count += 1
            print(f"✅ {key[:50]}")
        else:
            print(f"⚠️  {key[:50]} (无 token 数据)")
    
    # 保存状态
    state["imported_sessions"] = list(imported)
    state["last_import"] = datetime.now().isoformat()
    save_state(state)
    
    print(f"\n✅ 导入完成！成功导入 {success_count} 条记录")
    print(f"📈 累计导入：{len(imported)} 条记录")

if __name__ == "__main__":
    main()
