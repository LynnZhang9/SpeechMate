#!/bin/bash
# SpeechMate Host Server 启动脚本

cd "$(dirname "$0")"
cd host
uvicorn main:app --host 127.0.0.1 --port 8001
