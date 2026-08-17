#!/bin/bash
set -e

cd /workspace/backend

# 清理旧数据库并初始化种子数据
rm -f *.db 2>/dev/null || true
if [ ! -f .env ]; then
  cp .env.example .env
fi
sed -i 's/USE_SQLITE=false/USE_SQLITE=true/' .env

echo "=== 安装后端依赖 ==="
pip install -q -r requirements.txt 2>&1 | tail -5 || true

echo "=== 初始化种子数据 ==="
python seed.py 2>&1

echo "=== 启动后端 ==="
(
  python -c "
from app import create_app
app = create_app('production')
app.run(host='0.0.0.0', port=5000, debug=False)
" > /tmp/backend_full.log 2>&1
) &
BACK_PID=$!
echo "Backend PID=$BACK_PID"

echo "等待后端启动..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 1
  if curl -s http://127.0.0.1:5000/api/health > /dev/null 2>&1; then
    echo "Backend is up after ${i}s"
    break
  fi
  echo -n "."
done
echo ""

echo "--- 后端日志尾部 ---"
cat /tmp/backend_full.log | tail -5

echo ""
echo "=== 运行全流程测试 (test_api.py) ==="
cd /workspace
set +e
python3 test_api.py
TEST_EXIT=$?
set -e

echo ""
echo "=== 停止后端 ==="
kill $BACK_PID 2>/dev/null || true
sleep 1

echo ""
if [ $TEST_EXIT -eq 0 ]; then
  echo "所有测试通过"
  exit 0
else
  echo "测试失败，退出码=$TEST_EXIT"
  exit $TEST_EXIT
fi
