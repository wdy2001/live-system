#!/bin/bash
set -e

# 请在项目根目录下执行此脚本，步骤与 README 一致:
#   cd backend → pip install → seed → app.py
cd backend

echo "=== 安装 Python 依赖 ==="
pip install -r requirements.txt

echo ""
echo "=== 初始化数据库与种子数据 ==="
export USE_SQLITE=true
export FLASK_ENV=development
python seed.py

echo ""
echo "=== 启动后端服务 ==="
echo "服务将运行于 http://0.0.0.0:5000"
python app.py
