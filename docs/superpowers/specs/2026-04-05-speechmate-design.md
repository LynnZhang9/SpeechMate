# SpeechMate 设计文档

## 概述

SpeechMate 是一个本地运行的语音识别与翻译助手，面向个人用户（开发者/写作者）。

### 核心工作流

1. 用户按住快捷键（F8）开始录音（托盘图标变化指示）
2. 松开快捷键，录音发送到 Host Server
3. Host 调用 GLM API 进行语音识别
4. 可选：调用 GLM API 进行中英翻译
5. 结果通过剪贴板 + 粘贴自动输入到光标位置

### 目标用户

个人开发者、写作者，需要快速语音输入文字到各种应用。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    本地机器                              │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │   Client        │      │      Host Server        │  │
│  │   (PyQt5)       │ HTTP │      (FastAPI)          │  │
│  │                 │◄────►│                         │  │
│  │  - 系统托盘      │      │  - /api/speech 语音识别  │  │
│  │  - 热键监听      │      │  - /api/translate 翻译   │  │
│  │  - 录音功能      │      │  - /api/config 配置管理  │  │
│  │  - 剪贴板操作    │      │  - Web Admin (静态页面)  │  │
│  └─────────────────┘      └─────────────────────────┘  │
│                                    │                    │
│                                    ▼                    │
│                            ┌─────────────┐             │
│                            │   GLM API   │             │
│                            │  (智谱云端)  │             │
│                            └─────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Host Server (FastAPI)

- 端口：`8000`（可配置）
- 提供 REST API 给 Client 调用
- 内嵌 Web Admin 页面管理 API Key

### Client (PyQt5)

- 后台运行，系统托盘驻留
- 监听全局快捷键
- 通过 HTTP 调用 Host API

---

## API 设计

### 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/speech` | POST | 上传音频，返回识别文本 |
| `/api/translate` | POST | 发送文本，返回翻译结果 |
| `/api/config` | GET/PUT | 获取/更新 API Key 配置 |
| `/admin` | GET | Web Admin 页面 |

### 请求/响应格式

#### POST /api/speech

语音识别接口。

**请求：**
```
Content-Type: multipart/form-data
audio: <音频文件，格式为 WAV，采样率 16000Hz，单声道>
```

**响应：**
```json
{
  "text": "识别出的文本内容"
}
```

#### POST /api/translate

翻译接口。

**请求：**
```json
{
  "text": "需要翻译的文本",
  "target_lang": "en" | "zh"
}
```

**响应：**
```json
{
  "translated_text": "翻译后的文本"
}
```

#### GET /api/config

获取当前配置（API Key 脱敏显示）。

**响应：**
```json
{
  "api_key": "sk-xxx..."
}
```

#### PUT /api/config

更新配置。

**请求：**
```json
{
  "api_key": "sk-完整的API密钥"
}
```

**响应：**
```json
{
  "success": true
}
```

### 配置存储

配置文件存储位置：`~/.speechmate/config.json`

```json
{
  "api_key": "sk-xxx"
}
```

### 错误处理

所有 API 在出错时返回统一格式，HTTP 状态码为 4xx 或 5xx：

```json
{
  "error": "错误描述信息",
  "code": "ERROR_CODE"
}
```

**错误示例：**

```json
// API Key 未配置 (HTTP 400)
{
  "error": "API Key 未设置，请在 Web Admin 中配置",
  "code": "API_KEY_NOT_SET"
}

// API Key 无效 (HTTP 401)
{
  "error": "API Key 无效或已过期",
  "code": "API_KEY_INVALID"
}

// 音频为空 (HTTP 400)
{
  "error": "上传的音频文件为空",
  "code": "AUDIO_EMPTY"
}

// 语音识别失败 (HTTP 500)
{
  "error": "GLM API 调用失败: 连接超时",
  "code": "SPEECH_RECOGNITION_FAILED"
}

// 翻译失败 (HTTP 500)
{
  "error": "GLM API 调用失败: 配额不足",
  "code": "TRANSLATION_FAILED"
}
```

**错误码列表：**
| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `API_KEY_NOT_SET` | 400 | API Key 未配置 |
| `API_KEY_INVALID` | 401 | API Key 无效或过期 |
| `AUDIO_EMPTY` | 400 | 音频文件为空 |
| `AUDIO_FORMAT_ERROR` | 400 | 音频格式不支持 |
| `SPEECH_RECOGNITION_FAILED` | 500 | 语音识别服务调用失败 |
| `TRANSLATION_FAILED` | 500 | 翻译服务调用失败 |

---

## Client 设计

### 模块划分

```
client/
├── main.py              # 入口，启动应用
├── tray.py              # 系统托盘管理
├── hotkey.py            # 全局热键监听
├── recorder.py          # 录音功能
├── api_client.py        # 调用 Host API
├── clipboard.py         # 剪贴板操作
└── resources/
    └── icons/           # 托盘图标（正常/录音状态）
```

### 快捷键

固定为 `F8`，代码写死。

### 录音流程

1. 按下 F8 → 切换托盘图标 → 开始录音
2. 松开 F8 → 停止录音 → 恢复托盘图标
3. 调用 `/api/speech` 获取文本
4. 保存原剪贴板内容 → 写入识别文本 → 模拟 Ctrl+V/Cmd+V → 恢复原剪贴板

### 剪贴板操作细节

1. 保存当前剪贴板内容
2. 将识别/翻译结果写入剪贴板
3. 模拟粘贴快捷键（Windows: Ctrl+V, macOS: Cmd+V, Linux: Ctrl+V）
4. 短暂延迟后恢复原剪贴板内容

---

## Web Admin 设计

### 功能

- 配置 GLM API Key
- 保存配置

### 技术选型

- 前端：纯 HTML + CSS + JavaScript
- 托管：FastAPI 静态文件服务

### 页面布局

```
┌─────────────────────────────────────┐
│         SpeechMate Admin            │
├─────────────────────────────────────┤
│                                     │
│   GLM API Key                       │
│   ┌─────────────────────────────┐   │
│   │ sk-xxxxxxxxxxxxxxxxxxxx     │   │
│   └─────────────────────────────┘   │
│                                     │
│            [ 保存配置 ]              │
│                                     │
│   ✓ 保存成功                        │
└─────────────────────────────────────┘
```

---

## 项目结构

```
SpeechMate/
├── host/                      # Host Server
│   ├── main.py               # FastAPI 入口
│   ├── api/
│   │   ├── speech.py         # 语音识别接口
│   │   ├── translate.py      # 翻译接口
│   │   └── config.py         # 配置管理接口
│   ├── services/
│   │   ├── glm_client.py     # GLM API 封装
│   │   └── config_store.py   # 配置存储
│   ├── static/               # Web Admin 静态文件
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   └── requirements.txt
│
├── client/                    # Client 应用
│   ├── main.py               # PyQt5 入口
│   ├── tray.py               # 系统托盘
│   ├── hotkey.py             # 热键监听
│   ├── recorder.py           # 录音
│   ├── api_client.py         # HTTP 客户端
│   ├── clipboard.py          # 剪贴板操作
│   ├── resources/
│   │   └── icons/
│   │       ├── normal.png
│   │       └── recording.png
│   └── requirements.txt
│
├── docs/                      # 文档
│   └── README.md             # 使用说明
│
└── README.md                  # 项目说明
```

---

## 扩展点预留

以下功能本期不做，但在代码中预留接口：

| 功能 | 当前实现 | 预留方式 |
|------|----------|----------|
| 部署方式 | 仅本地（127.0.0.1） | API 基类设计为可配置 host 地址 |
| 翻译服务 | 仅 GLM | `TranslationService` 抽象类，便于添加其他实现 |
| 语音识别 | 仅 GLM API | `SpeechService` 抽象类，便于添加本地模型 |
| 快捷键配置 | 固定 F8 | 热键模块预留配置读取接口 |
| Web Admin 功能 | 仅 API Key | 页面预留统计/历史区域的占位 |
| 录音指示器 | 仅托盘图标 | 预留 `Indicator` 抽象类 |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Host Server | Python 3.10+ / FastAPI |
| Client | Python 3.10+ / PyQt5 |
| AI 服务 | GLM API（智谱） |
| Web Admin | 纯 HTML / CSS / JavaScript |
| 音频录制 | PyAudio / sounddevice |
| 剪贴板 | pyperclip |
| 热键 | pynput / PyQt5 QHotkey |

---

## MVP 功能清单

- [x] 语音识别（GLM API）
- [x] 中英翻译（GLM API）
- [x] 快捷键录音（固定 F8）
- [x] 托盘图标指示
- [x] 剪贴板自动输入
- [x] Web Admin 配置 API Key
