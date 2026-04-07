# 设计文档：切换回系统托盘

**日期**: 2026-04-07
**状态**: 已实现

## 背景

SpeechMate 最初使用系统托盘图标（`client/tray.py`），但由于 macOS Sequoia 早期版本的兼容性问题，改用了悬浮面板（`client/floating_panel.py`）。

用户当前系统为 macOS Sequoia 15.5，经验证系统托盘可正常工作，因此计划切换回系统托盘。

## 目标

- 使用系统托盘替代悬浮面板
- 保持所有现有功能不变
- 简化代码，删除不再使用的悬浮面板实现

## 改动范围

### 1. 修改 `client/tray.py`

添加 `floating_panel.py` 中有但 `tray.py` 缺失的功能：

**新增导入**
```python
from client.modes import WorkMode
```

**新增颜色常量**
```python
COLORS = {
    "ready": QColor(59, 130, 246),      # 蓝色 - 转录模式就绪
    "recording": QColor(239, 68, 68),   # 红色 - 录音中
    "processing": QColor(245, 158, 11), # 橙色 - 处理中
    "translate": QColor(76, 175, 80),   # 绿色 - 翻译模式就绪
}
```

**新增方法**

1. `set_processing(is_processing: bool)` - 设置处理中状态
   - 参数: `is_processing` - True 显示橙色图标
   - 行为: 切换图标颜色为橙色，tooltip 显示 "SpeechMate - Processing..."

2. `set_mode(mode: WorkMode)` - 设置工作模式
   - 参数: `mode` - `WorkMode.TRANSCRIBE` 或 `WorkMode.TRANSLATE`
   - 行为: 在就绪状态下，转录模式显示蓝色，翻译模式显示绿色

**修改 `set_recording` 方法**
- 录音结束后根据当前模式恢复对应颜色（而非固定蓝色）

### 2. 修改 `client/main.py`

**导入变更**
```python
# 改前
from client.floating_panel import create_tray_icon

# 改后
from client.tray import TrayIcon
```

**初始化变更**
```python
# 改前
self._tray = create_tray_icon()

# 改后
self._tray = TrayIcon()
```

### 3. 删除文件

- `client/floating_panel.py` - 悬浮面板实现，不再需要

## 接口兼容性

main.py 使用的所有接口在改动后保持兼容：

| 接口 | 来源 |
|------|------|
| `show()` | QSystemTrayIcon |
| `show_message(title, msg, icon, msecs)` | TrayIcon |
| `exit_requested` 信号 | TrayIcon |
| `config_requested` 信号 | TrayIcon |
| `set_recording(bool)` | TrayIcon |
| `set_mode(WorkMode)` | TrayIcon (新增) |
| `set_processing(bool)` | TrayIcon (新增) |
| `Warning` / `Critical` 常量 | QSystemTrayIcon |

## 图标状态

| 状态 | 颜色 | Tooltip |
|------|------|---------|
| 就绪（转录模式） | 蓝色 | SpeechMate |
| 就绪（翻译模式） | 绿色 | SpeechMate |
| 录音中 | 红色 | SpeechMate - Recording... |
| 处理中 | 橙色 | SpeechMate - Processing... |

## 风险

- macOS 未来更新可能再次破坏系统托盘功能
- 缓解措施：保留 `tray.py` 的 git 历史，必要时可恢复悬浮面板

## 测试计划

1. 启动应用，验证托盘图标正常显示
2. 按 Cmd+Shift+R，验证图标变红（录音中）
3. 释放热键，验证图标恢复蓝色（转录模式）
4. 按 Cmd+Shift+Y，验证图标变绿（翻译模式就绪）
5. 录音并释放，验证处理时图标变橙
6. 右键托盘图标，验证菜单正常
7. 验证通知消息正常显示
