#!/bin/bash
cd /workspace/backend
export FLASK_ENV=production
nohup python -c "
from app import create_app
app = create_app('production')
app.run(host='0.0.0.0', port=5000, debug=False)
" > /tmp/backend_final.log 2>&1 &
disown
echo "Started PID=$!"
sleep 4
echo "--- Log tail ---"
cat /tmp/backend_final.log | tail -10
echo "--- Process check ---"
ps -p $! -o pid,stat,cmd 2>/dev/null || echo "Process not found by ps -p"
pgrep -af "python.*app\|create_app" || echo "No python app processes found"
