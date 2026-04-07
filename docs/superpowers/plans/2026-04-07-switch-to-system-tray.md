# 切换回系统托盘 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 SpeechMate 从悬浮面板切换回系统托盘图标

**Architecture:** 修改现有 `tray.py` 添加缺失功能（set_processing, set_mode），修改 `main.py` 切换导入，删除 `floating_panel.py`

**Tech Stack:** Python 3, PyQt5, QSystemTrayIcon

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `client/tray.py` | 修改 | 添加 set_processing, set_mode 方法 |
| `client/main.py` | 修改 | 切换导入从 floating_panel 到 tray |
| `client/floating_panel.py` | 删除 | 不再需要 |

---

### Task 1: 修改 tray.py 添加新功能

**Files:**
- Modify: `client/tray.py`

- [ ] **Step 1: 添加 WorkMode 导入和颜色常量**

在文件顶部导入区域添加：

```python
from client.modes import WorkMode
```

在 `TrayIcon` 类中，`ICON_SIZE = 64` 下方添加颜色常量：

```python
    # Colors for different states
    COLORS = {
        "ready": QColor(59, 130, 246),      # Blue - transcribe mode
        "recording": QColor(239, 68, 68),   # Red
        "processing": QColor(245, 158, 11), # Orange
        "translate": QColor(76, 175, 80),   # Green - translate mode
    }
```

- [ ] **Step 2: 添加 _mode 实例变量**

在 `__init__` 方法中，`self._is_recording = False` 下方添加：

```python
        self._mode = WorkMode.TRANSCRIBE
```

- [ ] **Step 3: 创建 processing 图标**

在 `__init__` 方法中，修改图标创建部分。将：

```python
        # Create icons
        self._normal_icon = self._create_circle_icon(QColor(59, 130, 246))  # Blue
        self._recording_icon = self._create_circle_icon(QColor(239, 68, 68))  # Red
```

改为：

```python
        # Create icons
        self._normal_icon = self._create_circle_icon(self.COLORS["ready"])
        self._recording_icon = self._create_circle_icon(self.COLORS["recording"])
        self._processing_icon = self._create_circle_icon(self.COLORS["processing"])
        self._translate_icon = self._create_circle_icon(self.COLORS["translate"])
```

- [ ] **Step 4: 添加 set_processing 方法**

在 `set_recording` 方法下方添加：

```python
    def set_processing(self, is_processing: bool):
        """Set the processing state of the tray icon.

        Args:
            is_processing: True if processing, False if normal state.
        """
        if is_processing:
            self.setIcon(self._processing_icon)
            self.setToolTip("SpeechMate - Processing...")
        else:
            # Restore to current mode's icon
            self.set_mode(self._mode)
```

- [ ] **Step 5: 添加 set_mode 方法**

在 `set_processing` 方法下方添加：

```python
    def set_mode(self, mode: WorkMode):
        """Set the work mode of the tray icon.

        Args:
            mode: WorkMode.TRANSCRIBE or WorkMode.TRANSLATE
        """
        self._mode = mode
        if not self._is_recording:
            if mode == WorkMode.TRANSLATE:
                self.setIcon(self._translate_icon)
            else:
                self.setIcon(self._normal_icon)
            self.setToolTip("SpeechMate")
```

- [ ] **Step 6: 修改 set_recording 方法**

修改 `set_recording` 方法，使其在录音结束时恢复当前模式的颜色。将：

```python
    def set_recording(self, is_recording: bool):
        """Set the recording state of the tray icon.

        Args:
            is_recording: True if recording, False if normal state.
        """
        self._is_recording = is_recording
        if is_recording:
            self.setIcon(self._recording_icon)
            self.setToolTip("SpeechMate - Recording...")
        else:
            self.setIcon(self._normal_icon)
            self.setToolTip("SpeechMate")
```

改为：

```python
    def set_recording(self, is_recording: bool):
        """Set the recording state of the tray icon.

        Args:
            is_recording: True if recording, False if normal state.
        """
        self._is_recording = is_recording
        if is_recording:
            self.setIcon(self._recording_icon)
            self.setToolTip("SpeechMate - Recording...")
        else:
            # Restore to current mode's icon
            self.set_mode(self._mode)
```

- [ ] **Step 7: 提交 tray.py 修改**

```bash
git add client/tray.py
git commit -m "feat(tray): add set_processing and set_mode methods"
```

---

### Task 2: 修改 main.py 切换导入

**Files:**
- Modify: `client/main.py`

- [ ] **Step 1: 修改导入语句**

将第 19 行：

```python
from client.floating_panel import create_tray_icon
```

改为：

```python
from client.tray import TrayIcon
```

- [ ] **Step 2: 修改 _tray 初始化**

将第 50 行：

```python
        self._tray = create_tray_icon()
```

改为：

```python
        self._tray = TrayIcon()
```

- [ ] **Step 3: 提交 main.py 修改**

```bash
git add client/main.py
git commit -m "refactor(client): switch from floating panel to system tray"
```

---

### Task 3: 删除 floating_panel.py

**Files:**
- Delete: `client/floating_panel.py`

- [ ] **Step 1: 删除文件**

```bash
rm client/floating_panel.py
```

- [ ] **Step 2: 提交删除**

```bash
git add client/floating_panel.py
git commit -m "refactor(client): remove unused floating_panel.py"
```

---

### Task 4: 手动测试验证

**Files:**
- None (manual testing)

- [ ] **Step 1: 启动应用验证托盘图标**

```bash
python -m client.main
```

预期：托盘图标出现在菜单栏右侧，显示为蓝色圆点

- [ ] **Step 2: 测试录音状态**

按住 `Cmd+Shift+R`
预期：图标变红

释放热键
预期：图标恢复蓝色

- [ ] **Step 3: 测试翻译模式**

按 `Cmd+Shift+Y`
预期：图标变绿

- [ ] **Step 4: 测试右键菜单**

右键托盘图标
预期：显示菜单（打开设置、退出）

- [ ] **Step 5: 退出应用验证**

从菜单选择"退出"
预期：应用正常退出

---

### Task 5: 最终提交

- [ ] **Step 1: 确认所有更改已提交**

```bash
git status
git log --oneline -5
```

- [ ] **Step 2: 更新设计文档状态**

将设计文档中的 `**状态**: 待审核` 改为 `**状态**: 已实现`
