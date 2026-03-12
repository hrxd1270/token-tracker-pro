# Token Tracker Pro 📊

**Claude Code / LLM Token 使用统计工具** - 自动记录、分析和报告 token 消耗情况

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 特性

- 📊 **详细统计** - Token 消耗、速率、首 token 耗时 (TTFT)
- ✅ **成功/失败追踪** - 记录每次请求状态
- 📈 **实时报告** - 执行后立即生成使用报告
- 📅 **定时日报** - 每天早上自动发送使用报告
- 🔍 **历史查询** - 按天/周/月查看使用历史
- 📦 **多模型支持** - Claude Code、OpenAI、Qwen 等

---

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/token-tracker-pro.git
cd token-tracker-pro

# 添加别名到 ~/.bashrc 或 ~/.zshrc
echo 'alias claude-stat="python3 $(pwd)/src/claude-wrapper.py"' >> ~/.bashrc
source ~/.bashrc
```

### 使用

```bash
# 运行 Claude Code 并自动记录
claude-stat "帮我写个函数"

# 查看统计
claude-stat --stats

# 查看历史
claude-stat --history
```

---

## 📋 功能说明

### 核心工具

| 工具 | 说明 |
|------|------|
| `token-tracker-pro.py` | 核心记录工具 |
| `claude-wrapper.py` | Claude Code 包装器 |
| `claude-token-logger.py` | 日志解析器 |
| `claude-daily-report.py` | 日报生成器 |
| `claude-history-import.py` | **历史日志批量导入** ⭐ |
| `openclaw-session-import.py` | OpenClaw 会话导入 |

### 统计指标

- **Token 消耗** - 输入/输出 tokens
- **Token 速率** - tokens/秒
- **首 token 耗时 (TTFT)** - 第一次响应延迟
- **请求耗时** - 总耗时（秒）
- **成功/失败** - 请求状态 + 错误信息

---

## 📊 输出示例

```
🚀 执行 Claude Code: claude 帮我写个函数
------------------------------------------------------------
[Claude 输出内容...]

============================================================
📊 Claude Code 执行报告
============================================================
任务：帮我写个函数
时间：2026-03-12 17:15:30

📈 Token 使用:
  输入：5,200 tokens
  输出：1,300 tokens
  总计：6,500 tokens

⚡ 性能:
  首 token 耗时：1.45s
  Token 速率：620 tokens/s

✅ 状态：成功
============================================================
```

---

## 🔧 高级用法

### 手动记录

```bash
python3 src/token-tracker-pro.py log \
  --in 5000 --out 1000 \
  --model "claude-sonnet-4-5-20250929" \
  --task "代码审查" \
  --ttft 1.5 --duration 10.5 \
  --success true
```

### 查看统计

```bash
# 实时统计
python3 src/token-tracker-pro.py stats

# 最近 7 天
python3 src/token-tracker-pro.py stats --days 7

# 详细历史
python3 src/token-tracker-pro.py history --days 30 --limit 50
```

### 解析日志

```bash
# 从日志文件解析
python3 src/claude-token-logger.py \
  --log claude-output.log \
  --task "代码审查"
```

### 批量导入历史日志 ⭐

```bash
# 自动查找并导入 Claude Code 历史日志
python3 src/claude-history-import.py

# 预览模式（先看再导入）
python3 src/claude-history-import.py --dry-run

# 指定日志目录
python3 src/claude-history-import.py --dir ~/Documents/ClaudeLogs

# 只导入最近 30 天
python3 src/claude-history-import.py --days 30

# 查看完整文档
cat docs/claude-history-import-guide.md
```

**支持的日志格式**：
- Claude Code CLI 输出（`Tokens: 5.2k input, 1.2k output`）
- Anthropic API 响应（JSON 格式）
- 其他常见格式（`prompt_tokens=5200, completion_tokens=1200`）

**自动搜索目录**：
- `~/.claude/`
- `~/.config/Claude/`
- `~/Library/Logs/Claude/`
- `~/Library/Application Support/Claude/`
- `~/.local/share/Claude/`

---

### 导入 OpenClaw 历史会话

```bash
# 从 OpenClaw session 存储导入
python3 src/openclaw-session-import.py

# 只导入最近 7 天
python3 src/openclaw-session-import.py --days 7

# 预览模式
python3 src/openclaw-session-import.py --dry-run
```

---

## 📁 项目结构

```
token-tracker-pro/
├── src/
│   ├── token-tracker-pro.py          # 核心记录工具
│   ├── claude-wrapper.py             # Claude Code 包装器
│   ├── claude-token-logger.py        # 日志解析器
│   ├── claude-daily-report.py        # 日报生成器
│   ├── claude-history-import.py      # 历史日志批量导入 ⭐
│   └── openclaw-session-import.py    # OpenClaw 会话导入
├── examples/
│   └── usage-examples.md             # 使用示例
├── docs/
│   ├── advanced-guide.md             # 高级指南
│   ├── claude-history-import-guide.md # 历史日志导入指南 ⭐
│   └── import-guide.md               # OpenClaw 导入指南
├── README.md
├── LICENSE
└── requirements.txt
```

---

## 📅 定时任务

支持通过 cron 设置定时日报：

```bash
# 每天早上 9 点发送报告
openclaw cron add \
  --name "Token 日报" \
  --cron "0 9 * * *" \
  --tz "Asia/Shanghai" \
  --session "isolated" \
  --message "python3 src/claude-daily-report.py"
```

---

## 💡 最佳实践

### 日常使用

1. **统一使用包装器** - 所有 Claude Code 调用都通过 `claude-stat`
2. **定期检查统计** - 每周查看 token 使用情况
3. **分析性能** - 关注 TTFT 和 token 速率，优化 prompt
4. **记录任务类型** - 使用 `--task` 参数便于后续分析

### 历史日志导入

5. **首次导入先预览** - 使用 `--dry-run` 查看将要导入的内容
6. **按时间筛选** - 如果历史记录很多，先用 `--days 7` 测试
7. **定期导入** - 每周运行一次 `claude-history-import.py --days 7`
8. **备份数据** - 导入前备份 `token-usage-pro.json`

### 定时任务

9. **设置日报** - 每天早上自动发送使用报告
10. **定期备份** - 每周备份统计数据

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/YOUR_USERNAME/token-tracker-pro/issues)
- Email: your-email@example.com
