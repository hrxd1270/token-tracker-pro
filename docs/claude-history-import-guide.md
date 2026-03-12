# Claude Code 历史日志导入指南 📊

从 Claude Code 的历史日志文件中批量导入 token 使用记录。

---

## 🚀 快速开始

### 1. 下载脚本

```bash
# 从 GitHub 下载
git clone https://github.com/hrxd1270/token-tracker-pro.git
cd token-tracker-pro/src
```

### 2. 自动查找并导入

```bash
python3 claude-history-import.py
```

### 3. 查看统计

```bash
python3 token-tracker-pro.py stats
```

---

## 🔍 支持的日志格式

### Claude Code CLI 输出

```
Tokens: 5.2k input, 1.2k output
Duration: 10.5s
Time to first token: 1.5s
```

### Anthropic API 响应

```json
{
  "usage": {
    "input_tokens": 5200,
    "output_tokens": 1200
  }
}
```

### 其他格式

```
prompt_tokens=5200, completion_tokens=1200
Usage: 5.2k input, 1.2k output
```

---

## 🔧 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--dir` | 指定日志目录 | `--dir ~/claude-logs` |
| `--dry-run` | 预览模式 | `--dry-run` |
| `--days` | 只导入最近 N 天 | `--days 30` |
| `--tracker` | 指定 tracker 路径 | `--tracker ./token-tracker-pro.py` |

---

## 📋 使用示例

### 自动查找日志

```bash
# 在默认目录查找并导入
python3 claude-history-import.py
```

### 指定日志目录

```bash
# 从指定目录导入
python3 claude-history-import.py --dir ~/Documents/ClaudeLogs

# 多个目录
python3 claude-history-import.py \
  --dir ~/.claude \
  --dir ~/Library/Logs/Claude
```

### 预览模式

```bash
# 先看再导入
python3 claude-history-import.py --dry-run
```

### 只导入最近 30 天

```bash
python3 claude-history-import.py --days 30
```

---

## 📁 默认搜索目录

工具会自动在以下目录查找日志：

- `~/.claude/`
- `~/.config/Claude/`
- `~/Library/Logs/Claude/` (macOS)
- `~/Library/Application Support/Claude/` (macOS)
- `~/.local/share/Claude/` (Linux)
- 当前工作目录

---

## 📊 输出示例

### 预览模式

```
🔍 搜索日志文件...
📁 找到 15 个可能的日志文件

📄 解析日志文件...
  ✅ /home/user/.claude/session-001.log - 3 条记录
  ✅ /home/user/.claude/session-002.log - 5 条记录

📊 共解析 23 条记录

📋 预览导入内容:
================================================================================
2026-03-12 15:30 | claude-code       | 入:   5200 出:  1200 | 帮我写个排序函数
2026-03-12 14:15 | claude-code       | 入:  12000 出:  3500 | 代码审查
2026-03-12 10:00 | claude-code       | 入:   8000 出:  2000 | 单元测试生成
```

### 导入完成

```
🚀 开始导入到 token tracker...
✅ 导入完成！成功导入 23/23 条记录

📊 查看统计:
  python3 token-tracker-pro.py stats
  python3 token-tracker-pro.py history --days 30
```

---

## 📈 查看导入结果

### 查看统计

```bash
python3 token-tracker-pro.py stats --days 30
```

### 查看详细历史

```bash
python3 token-tracker-pro.py history --days 30 --limit 50
```

### 按模型统计

```bash
python3 token-tracker-pro.py stats
```

输出示例：

```
📊 Token 使用统计 (过去 30 天)
============================================================
📞 调用次数：45
✅ 成功：44 | ❌ 失败：1 | 成功率：97.8%
📥 总输入：250,000 tokens
📤 总输出：60,000 tokens
📈 总计：310,000 tokens

⚡ 性能指标:
  首 token 耗时 (TTFT): 1.52s
  平均请求耗时：10.35s
  平均 token 速率：870 tokens/s

📚 按模型统计:
  claude-code:
    调用：45 次 | 成功：44 | 失败：1
    输入：250,000 | 输出：60,000 | 总计：310,000
```

---

## 💡 最佳实践

### 1. 定期导入

建议每周运行一次导入：

```bash
# 每周日执行
python3 claude-history-import.py --days 7
```

### 2. 使用日志目录

设置 Claude Code 输出到固定目录：

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export CLAUDE_LOG_DIR=~/Documents/ClaudeLogs

# 使用别名
alias claude='claude | tee -a $CLAUDE_LOG_DIR/$(date +%Y%m%d).log'
```

### 3. 备份数据

导入前备份统计数据：

```bash
cp ~/.openclaw/workspace/data/token-usage-pro.json \
   ~/.openclaw/workspace/data/token-usage-pro.backup.$(date +%Y%m%d).json
```

---

## 🐛 故障排查

### 问题：找不到日志文件

```bash
# 手动指定目录
python3 claude-history-import.py --dir /path/to/your/logs

# 检查文件权限
ls -la ~/Documents/ClaudeLogs/
```

### 问题：解析不到 token 数据

检查日志格式是否匹配：

```bash
# 查看日志内容
cat your-log.log | grep -i "tokens\|usage\|prompt\|completion"
```

### 问题：重复导入

```bash
# 目前不支持去重，建议：
# 1. 使用 --days 参数限制时间范围
# 2. 导入前备份数据
# 3. 如有重复，手动清理 token-usage-pro.json
```

---

## 📝 完整工作流

```bash
# 1. 克隆项目
git clone https://github.com/hrxd1270/token-tracker-pro.git
cd token-tracker-pro/src

# 2. 预览
python3 claude-history-import.py --dry-run

# 3. 导入最近 30 天
python3 claude-history-import.py --days 30

# 4. 查看统计
python3 token-tracker-pro.py stats

# 5. 查看历史
python3 token-tracker-pro.py history --limit 30
```

---

现在你可以批量导入所有 Claude Code 历史记录了！🎉
