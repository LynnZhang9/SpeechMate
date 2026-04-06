# SpeechMate

SpeechMate 是一个本地运行的语音识别与翻译助手，面向个人用户（开发者/写作者）。

## 功能特性

- **语音识别** - 按住 **Cmd+Shift+R** 录音，松开后自动识别语音并转换为文字
- **中英翻译** - 支持中文翻译为英文，英文翻译为中文
- **自动粘贴** - 识别/翻译结果自动粘贴到光标位置
- **浮动面板** - 顶部悬浮窗显示录音状态（兼容 macOS Sequoia）
- **Web Admin** - 网页界面配置 API Key

## 系统要求

- Python 3.10+
- macOS / Windows / Linux
- 麦克风设备
- [智谱 GLM API Key](https://open.bigmodel.cn/)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd SpeechMate
```

### 2. 安装依赖

**Host Server:**
```bash
cd host
pip install -r requirements.txt
```

**Client:**
```bash
cd client
pip install -r requirements.txt
```

### 3. 配置 API Key

启动 Host Server 后，访问 http://127.0.0.1:8001/admin 配置你的 GLM API Key。

### 4. 运行

**启动 Host Server:**
```bash
# 方法1: 使用启动脚本
./run_host.sh

# 方法2: 手动启动
cd host
uvicorn main:app --host 127.0.0.1 --port 8001

# 开发模式（代码修改后自动重启）
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

**启动 Client:**
```bash
# 从项目根目录运行
python -m client.main

# 或者使用启动脚本
./run_client.sh
```

### 5. 使用

1. 确保屏幕右上角显示 SpeechMate 浮动面板（蓝色圆点 + "SM"）
2. 按住 **Cmd+Shift+R** 键开始录音（圆点变为红色）
3. 松开按键停止录音
4. 等待识别完成，文字自动粘贴到光标位置

## 项目结构

```
SpeechMate/
├── host/                      # Host Server (FastAPI)
│   ├── main.py               # 服务入口
│   ├── api/
│   │   ├── speech.py         # 语音识别接口
│   │   ├── translate.py      # 翻译接口
│   │   └── config.py         # 配置管理接口
│   ├── services/
│   │   ├── glm_client.py     # GLM API 封装
│   │   └── config_store.py   # 配置存储
│   ├── static/               # Web Admin 静态文件
│   └── requirements.txt
│
├── client/                    # Client 应用 (PyQt5)
│   ├── main.py               # 应用入口
│   ├── floating_panel.py     # 浮动面板（替代系统托盘）
│   ├── hotkey.py             # 热键监听（支持组合键）
│   ├── recorder.py           # 录音
│   ├── api_client.py         # HTTP 客户端
│   ├── clipboard.py          # 剪贴板操作
│   └── requirements.txt
│
├── docs/                      # 文档
│   └── README.md             # 使用说明
│
└── README.md                  # 项目说明
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/speech` | POST | 上传音频，返回识别文本 |
| `/api/translate` | POST | 发送文本，返回翻译结果 |
| `/api/config` | GET/PUT | 获取/更新 API Key 配置 |
| `/admin` | GET | Web Admin 页面 |
| `/health` | GET | 健康检查 |

## 开发指南

### 运行测试

**Host Server 测试:**
```bash
cd host
pytest
```

**Client 测试:**
```bash
cd client
pytest
```

### 配置文件

配置文件存储位置: `~/.speechmate/config.json`

```json
{
  "api_key": "sk-xxx"
}
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Host Server | Python 3.10+ / FastAPI |
| Client | Python 3.10+ / PyQt5 |
| AI 服务 | GLM API (智谱) - glm-asr 模型 |
| 音频录制 | sounddevice / soundfile |
| 剪贴板 | pyperclip |
| 热键 | pynput |
| HTTP 客户端 | requests |

## macOS 兼容性说明

### macOS Sequoia 15.x 注意事项

由于 macOS Sequoia 存在系统托盘图标不显示的问题，SpeechMate 使用**浮动面板**作为替代方案：

- 浮动面板显示在屏幕右上角
- 蓝色圆点 = 就绪状态
- 红色圆点 = 录音中
- 橙色圆点 = 处理中
- 点击面板可显示菜单

### macOS 权限配置

首次运行需要配置以下权限：

1. **辅助功能权限**（用于全局快捷键）
   - 系统设置 > 隐私与安全性 > 辅助功能
   - 添加终端或 Python 到允许列表

2. **麦克风权限**
   - 系统设置 > 隐私与安全性 > 麦克风
   - 允许终端访问麦克风

## License

MIT License

Copyright (c) 2026 SpeechMate

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
