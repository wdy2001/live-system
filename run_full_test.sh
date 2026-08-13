#!/bin/bash
set -e

# 在子shell中启动后端（后台运行）
(
  cd /workspace/backend
  export FLASK_ENV=production
  python -c "
from app import create_app
app = create_app('production')
app.run(host='0.0.0.0', port=5000, debug=False)
" > /tmp/backend_full.log 2>&1
) &
BACK_PID=$!
echo "Backend PID=$BACK_PID"

# 等待后端启动
echo "Waiting for backend..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 1
  if curl -s http://127.0.0.1:5000/api/health > /dev/null 2>&1; then
    echo "Backend is up after ${i}s"
    break
  fi
  echo -n "."
done
echo ""

# 显示后端日志
echo "--- Backend started, pid=$BACK_PID"
cat /tmp/backend_full.log | tail -3

# 1. 登录获取 token
echo "=== 1. LOGIN ==="
LOGIN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123"}')
LOGIN_OK=$(python3 -c "
import sys, json
try:
    d = json.loads(sys.argv[1])
    print('ok' if 'access_token' in d else json.dumps(d, ensure_ascii=False))
except:
    print('PARSE_ERR: ' + repr(sys.argv[1][:200]))
" "$LOGIN")
echo "--- LOGIN: $LOGIN_OK"
TOKEN=$(python3 -c "import sys,json; print(json.loads(sys.argv[1])['access_token'])" "$LOGIN")
AUTH="Authorization: Bearer $TOKEN"
echo "Token prefix: ${TOKEN:0:30}..."

# 2. Dashboard
echo "=== 2. DASHBOARD ==="
echo "--- GET /api/dashboard"
curl -s http://127.0.0.1:5000/api/dashboard -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('keys:', sorted(d.keys()))
print('unpaid_total:', d.get('unpaid_total'))
trends = d.get('trends') or d.get('monthly_usage') or []
print('monthly_usage/trends len:', len(trends))
"

# 3. Payment: unpaid bills (electricity)
echo "=== 3. UNPAID ELECTRICITY BILLS ==="
echo "--- GET /api/bills?status=unpaid&type=electricity"
curl -s "http://127.0.0.1:5000/api/bills?status=unpaid&type=electricity" -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
b = d.get('bills', [])
print(f'count={len(b)}')
for x in b[:3]:
    print(f\"  - id={x['id']} period={x['period']} amount={x['amount']} type={x['type']} status={x['status']}\")
"

# 4. Records: paid bills (with pagination)
echo "=== 4. PAID BILLS PAGINATION ==="
echo "--- GET /api/bills?status=paid&page=1&per_page=2"
curl -s "http://127.0.0.1:5000/api/bills?status=paid&page=1&per_page=2" -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
types_list = [x['type'] for x in d.get('bills', [])]
print(f\"total={d.get('total')}, returned={len(d.get('bills',[]))}, types={types_list}\")
"

# 5. Bill detail (first unpaid bill) - 验证 breakdown
echo "=== 5. BILL DETAIL ==="
FIRST_UNPAID=$(curl -s "http://127.0.0.1:5000/api/bills?status=unpaid&per_page=1" -H "$AUTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['bills'][0]['id'])")
echo "First unpaid id: $FIRST_UNPAID"
echo "--- GET /api/bills/$FIRST_UNPAID (detail)"
curl -s "http://127.0.0.1:5000/api/bills/$FIRST_UNPAID" -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)['bill']
print(f\"id={d['id']} amount={d['amount']} status={d['status']}\")
bd = d.get('breakdown') or []
print(f'breakdown tiers={len(bd)}')
s = sum(b['subtotal'] for b in bd)
print(f'subtotal_sum={s:.2f}, bill_amount={d[\"amount\"]:.2f}, match={abs(s - d[\"amount\"]) < 0.02}')
"

# 6. Pay a bill
echo "=== 6. PAY BILL ==="
echo "--- POST /api/bills/$FIRST_UNPAID/pay (模拟支付)"
curl -s -X POST "http://127.0.0.1:5000/api/bills/$FIRST_UNPAID/pay" \
  -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d '{"method":"wechat"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
p = d.get('payment')
b = d.get('bill')
tx = p.get('transaction_no') if p else None
print(f'transaction_no={tx} (starts with PAY? {tx.startswith(\"PAY\") if tx else False})')
status = b.get('status') if b else None
paid_at = b.get('paid_at') if b else None
print(f'bill.status now={status}, paid_at set={bool(paid_at) if paid_at is not None else None}')
"

# 7. 刷新 unpaid 列表
echo "=== 7. REFRESH UNPAID ==="
echo "--- GET /api/bills?status=unpaid 再次刷新"
curl -s "http://127.0.0.1:5000/api/bills?status=unpaid&per_page=50" -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ids = [b['id'] for b in d.get('bills', [])]
print(f'unpaid count now={len(ids)}')
"

# 停止后端
kill $BACK_PID 2>/dev/null
sleep 1
echo "--- Done ---"
