# 高级指南

## 数据格式

### token-usage-pro.json

```json
{
  "records": [
    {
      "timestamp": "2026-03-12T17:09:00",
      "tokens_in": 5000,
      "tokens_out": 1000,
      "tokens_total": 6000,
      "model": "claude-sonnet-4-5-20250929",
      "task": "代码审查",
      "ttft": 1.5,
      "duration": 10.5,
      "token_rate": 571.43,
      "success": true,
      "error_msg": null
    }
  ],
  "total": {
    "in": 6000,
    "out": 1000,
    "calls": 1,
    "success": 1,
    "failed": 0
  }
}
```

## 自定义分析

### 按任务类型分析

```python
import json
from pathlib import Path

data_file = Path.home() / ".openclaw" / "workspace" / "data" / "token-usage-pro.json"

with open(data_file) as f:
    data = json.load(f)

# 按任务分组
tasks = {}
for record in data["records"]:
    task = record.get("task", "未知")
    if task not in tasks:
        tasks[task] = {"calls": 0, "tokens": 0}
    tasks[task]["calls"] += 1
    tasks[task]["tokens"] += record["tokens_total"]

# 输出
for task, stats in sorted(tasks.items(), key=lambda x: x[1]["tokens"], reverse=True):
    print(f"{task}: {stats['calls']} 次，{stats['tokens']:,} tokens")
```

### 按时间段分析

```python
from datetime import datetime, timedelta

# 筛选最近 7 天
now = datetime.now()
cutoff = now - timedelta(days=7)

recent_records = [
    r for r in data["records"]
    if datetime.fromisoformat(r["timestamp"]) >= cutoff
]

total_tokens = sum(r["tokens_total"] for r in recent_records)
print(f"最近 7 天消耗：{total_tokens:,} tokens")
```

## 集成到其他工具

### 包装其他 LLM CLI 工具

```bash
#!/bin/bash
# openai-stat - OpenAI CLI 包装器

START_TIME=$(date +%s.%N)
TASK="${1:-OpenAI 调用}"

# 运行并捕获输出
output=$(openai "$@" 2>&1)
echo "$output"

# 解析 token 使用（根据实际输出格式调整）
tokens_in=$(echo "$output" | grep -oP 'prompt_tokens: \K\d+')
tokens_out=$(echo "$output" | grep -oP 'completion_tokens: \K\d+')

# 记录
python3 src/token-tracker-pro.py log \
  --in "${tokens_in:-0}" \
  --out "${tokens_out:-0}" \
  --model "gpt-4" \
  --task "$TASK" \
  --success true
```

### API 调用统计

```python
# 包装 HTTP 请求
import requests
import time
import subprocess

def tracked_request(url, data, task="API 调用"):
    start = time.time()
    response = requests.post(url, json=data)
    duration = time.time() - start
    
    # 估算 token（简单方法）
    tokens_in = len(str(data)) // 4
    tokens_out = len(response.text) // 4
    
    # 记录
    subprocess.run([
        "python3", "src/token-tracker-pro.py", "log",
        "--in", str(tokens_in),
        "--out", str(tokens_out),
        "--model", "api",
        "--task", task,
        "--duration", str(duration)
    ])
    
    return response
```

## 性能优化建议

### 1. 减少 Token 消耗

- **精简 prompt** - 移除不必要的上下文
- **使用系统消息** - 将固定指令放在 system role
- **限制输出长度** - 设置 `max_tokens` 参数
- **分批处理** - 大任务拆分成小请求

### 2. 提高响应速度

- **选择合适模型** - 小任务用小模型
- **流式输出** - 使用 stream 模式
- **并发请求** - 多个独立请求并发执行
- **缓存结果** - 相同请求返回缓存

### 3. 监控告警

```python
# 检查是否超过阈值
def check_threshold(daily_limit=100000):
    from datetime import datetime, timedelta
    
    data = load_data()
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0)
    
    today_tokens = sum(
        r["tokens_total"] for r in data["records"]
        if datetime.fromisoformat(r["timestamp"]) >= today_start
    )
    
    if today_tokens > daily_limit:
        print(f"⚠️  今日消耗 {today_tokens:,} tokens，超过限制 {daily_limit:,}")
        # 发送告警
        send_alert(f"Token 消耗告警：{today_tokens:,}/{daily_limit:,}")
```

## 数据备份

### 自动备份脚本

```bash
#!/bin/bash
# backup-token-data.sh

BACKUP_DIR=~/backups/token-tracker
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"
cp ~/.openclaw/workspace/data/token-usage-pro.json "$BACKUP_DIR/token-usage-$DATE.json"

# 保留最近 30 天
find "$BACKUP_DIR" -name "*.json" -mtime +30 -delete

echo "✅ 备份完成：$BACKUP_DIR/token-usage-$DATE.json"
```

### 导出为 CSV

```python
import csv
import json
from datetime import datetime

def export_to_csv(output_file="usage.csv"):
    with open("token-usage-pro.json") as f:
        data = json.load(f)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            '时间', '模型', '任务', '输入', '输出', '总计', 
            'TTFT', '耗时', '速率', '状态'
        ])
        
        for r in data["records"]:
            writer.writerow([
                r["timestamp"],
                r["model"],
                r.get("task", ""),
                r["tokens_in"],
                r["tokens_out"],
                r["tokens_total"],
                r.get("ttft", ""),
                r.get("duration", ""),
                r.get("token_rate", ""),
                "成功" if r.get("success", True) else "失败"
            ])
    
    print(f"✅ 导出完成：{output_file}")
```
