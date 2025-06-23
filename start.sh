#!/bin/bash

# 下载 spaCy 英文模型
python -m spacy download en_core_web_sm

# 启动 Flask SocketIO 应用
python app.py