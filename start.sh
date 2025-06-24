#!/bin/bash
python -m spacy download en_core_web_sm
# 初始化数据库（只在第一次生效）
#python init_db.py
python app.py