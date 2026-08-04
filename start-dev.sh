#!/usr/bin/env bash
set -e
echo "🚀 启动开发模式（SQLite）..."
echo "后端: http://localhost:5000  前端: http://localhost:5173"
(cd backend && USE_SQLITE=true python app.py) &
BACK_PID=$!
(npm run dev) &
FRONT_PID=$!
trap "kill $BACK_PID $FRONT_PID 2>/dev/null; echo '✨ 已停止前后端'" INT TERM EXIT
wait
