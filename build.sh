#!/bin/bash
# 安装依赖
pip install -r requirements.txt

# 创建数据库目录
mkdir -p db

# 初始化数据库
python init_db.py