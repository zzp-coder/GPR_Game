#!/bin/bash
python -m spacy download en_core_web_sm

# 如果设置了 INIT_DB=True 就执行初始化脚本
if [ "$INIT_DB" = "true" ]; then
  echo "🛠 Initializing database..."
  python init_db.py
else
  echo "✅ Skipping database initialization"
fi

# 启动应用
python app.py