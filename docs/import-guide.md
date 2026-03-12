# 存量日志导入指南 📊

从 OpenClaw 历史会话中批量导入 token 使用记录。

---

## 🚀 快速开始

### 导入所有历史会话

```bash
python3 src/openclaw-session-import.py
```

### 只导入最近 N 天

```bash
# 最近 7 天
python3 src/openclaw-session-import.py --days 7

# 最近 30 天
python3 src/openclaw-session-import.py --days 30
```

### 预览模式（不实际导入）

```bash
python3 src/openclaw-session-import.py --dry-run
```

---

## 📋 功能说明

### 自动解析

工具会自动从 OpenClaw 的 session 存储中解析：
- ✅ 输入/输出 token 数
- ✅ 模型名称
- ✅ 任务类型（cron 任务/QQ 对话等）
- ✅ 时间戳

### 智能去重

- 自动记录已导入的会话
- 避免重复导入
- 支持增量导入

### 状态持久化

导入状态保存在：`~/.openclaw/workspace/data/session-import-state.json`

---

## 🔧 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--days` | 只导入最近 N 天 | `--days 7` |
| `--dry-run` | 预览模式，不实际导入 | `--dry-run` |
| `--reset` | 重置导入状态 | `--reset` |

---

## 📊 输出示例

### 预览模式

```
📊 获取会话列表...
📈 发现 7 个会话
📥 待导入：7 个会话

📋 预览导入内容:
================================================================================
2026-03-12 19:09 | qwen3.5-plus         | 入: 449110 出:   741 | QQ 对话
2026-03-12 10:00 | qwen3.5-plus         | 入:  50806 出:   569 | 每日笑话推送
2026-03-12 10:00 | qwen3.5-plus         | 入:  50806 出:   569 | 每日笑话推送
2026-03-11 10:00 | qwen3.5-plus         | 入:  14839 出:   558 | QQ 对话
```

### 导入完成

```
🚀 开始导入...
✅ agent:main:qqbot:direct:06236e781161f14355309b3cd7
✅ agent:main:cron:11ea49ff-16a1-4132-a340-8d7995b752
✅ agent:main:cron:11ea49ff-16a1-4132-a340-8d7995b752

✅ 导入完成！成功导入 7 条记录
📈 累计导入：7 条记录
```

---

## 📈 查看导入结果

### 查看统计

```bash
python3 src/token-tracker-pro.py stats --days 30
```

### 查看历史

```bash
python3 src/token-tracker-pro.py history --days 30 --limit 20
```

---

## 🔄 重新导入

如果需要重新导入（比如修复了数据）：

```bash
# 重置导入状态
python3 src/openclaw-session-import.py --reset

# 重新导入
python3 src/openclaw-session-import.py
```

---

## 💡 最佳实践

1. **首次使用先预览**：`--dry-run` 查看将要导入的内容
2. **按时间筛选**：如果历史记录很多，先用 `--days 7` 测试
3. **定期检查**：每周运行一次导入新增的会话
4. **备份数据**：导入前备份 `token-usage-pro.json`

---

## 📝 任务类型识别

工具会自动识别任务类型：

| Session Key 包含 | 识别为 |
|-----------------|--------|
| `cron:11ea49ff` | 每日笑话推送 |
| `cron:0d772d9d` | Token 使用日报 |
| `cron:474c35ea` | Claude Code 日报 |
| `cron:*` | cron 任务 |
| `qqbot:*` | QQ 对话 |
| 其他 | kind 字段值 |

---

## 🐛 故障排查

### 问题：找不到 openclaw 命令

```bash
# 检查 openclaw 是否安装
which openclaw

# 如果没有，需要添加环境变量或完整路径
export PATH=$PATH:~/.local/share/pnpm
```

### 问题：导入的数据不对

```bash
# 查看导入状态
cat ~/.openclaw/workspace/data/session-import-state.json

# 重置并重新导入
python3 src/openclaw-session-import.py --reset
python3 src/openclaw-session-import.py
```

---

## 📊 完整工作流

```bash
# 1. 预览
python3 src/openclaw-session-import.py --dry-run

# 2. 导入最近 7 天测试
python3 src/openclaw-session-import.py --days 7

# 3. 查看结果
python3 src/token-tracker-pro.py stats --days 7

# 4. 导入所有
python3 src/openclaw-session-import.py

# 5. 查看完整统计
python3 src/token-tracker-pro.py stats
```

---

现在你的 token 统计系统已经包含了所有历史数据！🎉
