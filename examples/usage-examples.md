# 使用示例

## 基础用法

### 1. 运行 Claude Code 并记录

```bash
# 简单用法
python3 src/claude-wrapper.py "帮我写一个排序函数"

# 指定文件
python3 src/claude-wrapper.py --file main.py "优化这个代码"

# 指定任务描述
python3 src/claude-wrapper.py -t "代码审查" --file app.py "检查潜在问题"
```

### 2. 查看统计

```bash
# 查看所有统计
python3 src/claude-wrapper.py --stats

# 查看最近 7 天
python3 src/token-tracker-pro.py stats --days 7

# 查看最近 30 天
python3 src/token-tracker-pro.py stats --days 30
```

### 3. 查看历史

```bash
# 最近 10 条记录
python3 src/claude-wrapper.py --history

# 最近 50 条记录
python3 src/token-tracker-pro.py history --limit 50
```

---

## 进阶用法

### 手动记录其他 LLM 调用

```bash
# OpenAI
python3 src/token-tracker-pro.py log \
  --in 3000 --out 800 \
  --model "gpt-4-turbo" \
  --task "文章生成" \
  --ttft 2.1 --duration 8.5 \
  --success true

# Qwen
python3 src/token-tracker-pro.py log \
  --in 50000 --out 500 \
  --model "qwen3.5-plus" \
  --task "每日笑话推送" \
  --ttft 1.2 --duration 5.3 \
  --success true
```

### 解析日志文件

```bash
# 从 Claude Code 日志解析
python3 src/claude-token-logger.py \
  --log claude-output.log \
  --task "代码审查" \
  --model "claude-sonnet-4-5-20250929"
```

### 导出数据

```bash
# 导出 JSON 数据
cat ~/.openclaw/workspace/data/token-usage-pro.json | jq . > token-export.json

# 导出为 CSV（需要额外脚本）
python3 scripts/export-csv.py --days 30 --output usage.csv
```

---

## 定时任务

### OpenClaw Cron

```bash
# 每天早上 9 点发送日报
openclaw cron add \
  --name "Token 日报" \
  --cron "0 9 * * *" \
  --tz "Asia/Shanghai" \
  --session "isolated" \
  --message "python3 src/claude-daily-report.py" \
  --announce \
  --channel "qqbot" \
  --to "YOUR_USER_ID"
```

### System Cron

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 1 点备份数据
0 1 * * * cp ~/.openclaw/workspace/data/token-usage-pro.json /backup/token-$(date +\%Y\%m\%d).json
```

---

## 输出示例

### 统计输出

```
📊 Token 使用统计 (过去 7 天)
============================================================
📞 调用次数：15
✅ 成功：14 | ❌ 失败：1 | 成功率：93.3%
📥 总输入：75,000 tokens
📤 总输出：15,000 tokens
📈 总计：90,000 tokens
📉 平均每次：输入=5000, 输出=1000

⚡ 性能指标:
------------------------------------------------------------
  首 token 耗时 (TTFT): 1.52s
  平均请求耗时：10.35s
  平均 token 速率：870 tokens/s

📚 按模型统计:
------------------------------------------------------------
  claude-sonnet-4-5-20250929:
    调用：15 次 | 成功：14 | 失败：1
    输入：75,000 | 输出：15,000 | 总计：90,000
```

### 历史输出

```
📜 最近使用记录 (过去 7 天，最多 20 条)
================================================================================
03-12 17:09 ✅ | claude-sonnet-4-5-20 | 入：5000 出：1000 | TTFT:1.5s | 571t/s | 代码审查
03-12 16:45 ✅ | qwen3.5-plus         | 入：50000 出：500 | TTFT:1.2s | 850t/s | 每日笑话推送
03-12 14:30 ✅ | gpt-4-turbo          | 入：3000 出：800  | TTFT:2.1s | 450t/s | 文章生成
```

### 日报输出

```
📊 Claude Code 使用日报 (03-11)
============================================================
📞 调用次数：5
✅ 成功：5 | ❌ 失败：0 | 成功率：100%
📥 输入：25,000 tokens
📤 输出：5,000 tokens
📈 总计：30,000 tokens

⚡ 性能指标:
  首 token 耗时：1.48s
  平均速率：620 tokens/s

📁 任务统计:
  • 代码审查：2 次 | 12,000 tokens
  • 单元测试：2 次 | 10,000 tokens
  • 文档生成：1 次 | 8,000 tokens

============================================================
📈 累计统计:
  总调用：20 次 | 成功率：95%
  总消耗：120,000 tokens
  (输入：100,000 / 输出：20,000)
```

---

## 故障排查

### 问题：找不到 Python3

```bash
# 检查 Python 版本
python3 --version

# 如果未安装，使用系统包管理器安装
# Ubuntu/Debian
sudo apt install python3

# CentOS/RHEL
sudo yum install python3

# macOS
brew install python3
```

### 问题：权限错误

```bash
# 添加执行权限
chmod +x src/*.py
```

### 问题：数据文件不存在

```bash
# 首次运行会自动创建
# 检查数据目录
ls -la ~/.openclaw/workspace/data/

# 手动创建
mkdir -p ~/.openclaw/workspace/data
```
