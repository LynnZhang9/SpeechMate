# SpeechMate 使用说明

## 快捷键

### Cmd+Shift+R - 语音识别

| 操作 | 说明 |
|------|------|
| 按住 Cmd+Shift+R | 开始录音（浮动面板变为红色） |
| 松开 Cmd+Shift+R | 停止录音，发送到服务器识别 |

**工作流程:**
1. 按住 Cmd+Shift+R 键
2. 对着麦克风说话
3. 松开 Cmd+Shift+R 键
4. 等待识别完成
5. 识别的文字自动粘贴到当前光标位置

### Cmd+Shift+Y - 语音翻译

| 操作 | 说明 |
|------|------|
| 按住 Cmd+Shift+Y | 开始录音（浮动面板变为红色） |
| 松开 Cmd+Shift+Y | 停止录音，识别并翻译 |

**工作流程:**
1. 按住 Cmd+Shift+Y 键
2. 对着麦克风说话（中文或英文）
3. 松开 Cmd+Shift+Y 键
4. 等待识别和翻译完成
5. 结果自动粘贴到光标位置（格式：原文 + 换行 + 译文）

**语言自动检测:**
- 说中文 → 翻译成英文
- 说英文 → 翻译成中文

## 浮动面板

SpeechMate 启动后会在屏幕右上角显示浮动面板。

### 面板状态

| 状态 | 颜色 | 说明 |
|------|------|------|
| 就绪（识别模式） | 蓝色 | 程序就绪，可以使用 Cmd+Shift+R |
| 就绪（翻译模式） | 绿色 | 程序就绪，可以使用 Cmd+Shift+Y |
| 录音 | 红色 | 正在录音中 |
| 处理 | 橙色 | 正在识别/翻译音频 |

### 面板交互

- **点击面板** - 显示菜单
- **拖动面板** - 移动位置

### 面板菜单

点击面板可看到以下选项:

- **打开设置** - 打开 Web Admin 配置页面
- **状态: 就绪/录音中/处理中** - 当前状态（不可点击）
- **退出** - 关闭程序

### 通知消息

浮动面板会显示以下通知:

| 通知 | 说明 |
|------|------|
| "Ready" | 程序启动成功 |
| "Processing..." | 正在识别音频 |
| "识别中..." | 正在识别音频（翻译模式） |
| "翻译中..." | 正在翻译文本 |
| "翻译完成" | 翻译成功并已粘贴 |
| "Pasted: xxx" | 识别完成并已粘贴 |
| "No audio recorded" | 没有录到音频 |
| "No speech detected" | 没有检测到语音 |
| "翻译失败，已输出原文" | 翻译失败，但仍输出识别的原文 |
| "Error: ..." | 发生错误 |

## Web Admin

Web Admin 是一个网页界面，用于配置 GLM API Key。

### 访问地址

```
http://127.0.0.1:8001/admin
```

### 配置 API Key

1. 访问 Web Admin 页面
2. 在输入框中粘贴你的 GLM API Key
3. 点击"保存配置"按钮
4. 看到"保存成功"提示表示配置完成

### 获取 API Key

1. 访问 [智谱开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 在控制台创建 API Key

## 故障排除

### 代码修改后页面显示 "Not Found"

**症状:** 修改代码后访问页面显示 `{"detail":"Not Found"}`

**原因:** 服务器正在运行旧版本的代码

**解决方案:**

重启 Host Server 以加载最新代码：

```bash
# 方法1: 停止并重启
# 先按 Ctrl+C 停止当前服务器，然后重新启动
cd host
uvicorn main:app --host 127.0.0.1 --port 8001

# 方法2: 开发模式（推荐）
# 使用 --reload 参数，代码修改后自动重启
cd host
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### 无法连接到服务器

**症状:** 显示 "Network error - server unreachable"

**解决方案:**
1. 确保 Host Server 正在运行:
   ```bash
   cd host
   python -m uvicorn main:app --host 127.0.0.1 --port 8001
   ```
2. 检查端口 8001 是否被占用
3. 确认防火墙没有阻止本地连接
4. 如果你使用了系统代理，SpeechMate 已配置为自动绕过代理

### API Key 无效

**症状:** 识别失败，提示 "API Key 无效或已过期"

**解决方案:**
1. 访问 Web Admin 检查 API Key 是否正确
2. 确认 API Key 没有过期
3. 确认账户余额充足

### 没有录到音频

**症状:** 提示 "No audio recorded"

**解决方案:**
1. 检查麦克风是否连接
2. 检查系统是否允许 SpeechMate 访问麦克风
3. 检查系统音量设置中麦克风是否静音

### 识别结果为空

**症状:** 提示 "No speech detected"

**解决方案:**
1. 靠近麦克风说话
2. 说话声音大一些
3. 检查麦克风输入音量设置

### 快捷键不工作

**症状:** 按 Cmd+Shift+R 没有反应

**解决方案:**
1. 确保 SpeechMate Client 正在运行
2. 检查是否有其他程序占用了该快捷键
3. 尝试重启 SpeechMate Client
4. 确认已授予辅助功能权限（macOS）

### 自动粘贴不工作

**症状:** 识别成功但没有自动粘贴

**解决方案:**
1. 确保目标应用支持粘贴操作
2. 检查目标应用是否有焦点
3. 检查系统是否允许 SpeechMate 控制键盘

### macOS 权限问题

**症状:** macOS 上麦克风或快捷键不工作，或提示 `This process is not trusted!`

**解决方案:**

1. 打开 **系统设置** > **隐私与安全性** > **辅助功能**
2. 点击左下角 🔒 锁图标并输入密码解锁
3. 点击 **+** 按钮或找到列表中的 **终端**（Terminal）
4. 如果没有，点击 **+** 浏览 `/Applications/Utilities/Terminal.app` 添加
5. 勾选终端旁边的复选框
6. **重启终端** 并重新运行 SpeechMate Client

**麦克风权限:**
1. 打开 **系统设置** > **隐私与安全性** > **麦克风**
2. 确保终端已被允许访问麦克风

**注意:** macOS Ventura 及更新版本使用"系统设置"，旧版本使用"系统偏好设置"

### Windows 权限问题

**症状:** Windows 上功能不正常

**解决方案:**
1. 以管理员身份运行
2. 检查 Windows 安全中心是否阻止了程序

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `API_KEY_NOT_SET` | API Key 未配置 | 在 Web Admin 中配置 API Key |
| `API_KEY_INVALID` | API Key 无效 | 检查 API Key 是否正确 |
| `AUDIO_EMPTY` | 音频为空 | 检查麦克风是否正常工作 |
| `AUDIO_FORMAT_ERROR` | 音频格式错误 | 内部错误，重启程序 |
| `SPEECH_RECOGNITION_FAILED` | 语音识别失败 | 检查网络连接和 API 状态 |
| `TRANSLATION_FAILED` | 翻译失败 | 检查网络连接和 API 状态 |

## 日志查看

如需查看详细日志，可在终端中运行程序:

```bash
python -m client.main
```

终端会显示程序运行日志，包括错误信息。

## 端口说明

SpeechMate 使用以下端口：

| 端口 | 用途 |
|------|------|
| 8001 | Host Server API 服务 |

如果端口被占用，可以在启动时指定其他端口：

```bash
# Host Server
cd host
uvicorn main:app --host 127.0.0.1 --port 8002

# 同时需要修改 client/api_client.py 中的 DEFAULT_HOST
```
