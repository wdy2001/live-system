#!/bin/bash
set -e

echo "--- Backend started, pid=$!"
sleep 2
cat /tmp/backend2.log | tail -5

# 1. 登录获取 token
echo "=== STEP 1: LOGIN ==="
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123"}')
echo "Raw response: $LOGIN_RESPONSE"
LOGIN_STATUS=$(python3 << 'PYEOF'
import sys, json
try:
    d = json.loads(sys.argv[1])
    if "access_token" in d:
        print("ok")
    else:
        print(json.dumps(d, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}, raw={sys.argv[1]}")
PYEOF
)
echo "--- LOGIN: $LOGIN_STATUS"

TOKEN=$(python3 -c "import sys,json; print(json.loads(sys.argv[1])['access_token'])" "$LOGIN_RESPONSE")
AUTH="Authorization: Bearer $TOKEN"
echo "Token prefix: ${TOKEN:0:20}..."

# 2. Dashboard
echo "=== STEP 2: DASHBOARD ==="
echo "--- GET /api/dashboard"
DASH_RESP=$(curl -s http://localhost:5000/api/dashboard -H "$AUTH")
python3 << PYEOF
import sys, json
d = json.loads('''$DASH_RESP''')
print("keys:", sorted(d.keys()))
print("unpaid_total:", d.get("unpaid_total"))
trends = d.get("trends") or d.get("monthly_usage") or []
print("monthly_usage/trends len:", len(trends))
PYEOF

# 3. Payment: unpaid bills (electricity)
echo "=== STEP 3: UNPAID ELECTRICITY BILLS ==="
echo "--- GET /api/bills?status=unpaid&type=electricity"
BILLS_ELEC=$(curl -s "http://localhost:5000/api/bills?status=unpaid&type=electricity" -H "$AUTH")
python3 << PYEOF
import sys, json
d = json.loads('''$BILLS_ELEC''')
b = d["bills"]
print(f"count={len(b)}")
for x in b[:3]:
    print(f"  - id={x['id']} period={x['period']} amount={x['amount']} type={x['type']} status={x['status']}")
PYEOF

# 4. Records: paid bills (with pagination)
echo "=== STEP 4: PAID BILLS PAGINATION ==="
echo "--- GET /api/bills?status=paid&page=1&per_page=2"
PAID_BILLS=$(curl -s "http://localhost:5000/api/bills?status=paid&page=1&per_page=2" -H "$AUTH")
python3 << PYEOF
import sys, json
d = json.loads('''$PAID_BILLS''')
print(f"total={d['total']}, returned={len(d['bills'])}, types={[x['type'] for x in d['bills']]}")
PYEOF

# 5. Bill detail (first unpaid bill) - 验证 breakdown
echo "=== STEP 5: BILL DETAIL ==="
FIRST_UNPAID_ID=$(curl -s "http://localhost:5000/api/bills?status=unpaid&per_page=1" -H "$AUTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['bills'][0]['id'])")
echo "First unpaid bill id: $FIRST_UNPAID_ID"
echo "--- GET /api/bills/$FIRST_UNPAID_ID (detail)"
BILL_DETAIL=$(curl -s "http://localhost:5000/api/bills/$FIRST_UNPAID_ID" -H "$AUTH")
python3 << PYEOF
import sys, json
d = json.loads('''$BILL_DETAIL''')["bill"]
print(f"id={d['id']} amount={d['amount']} status={d['status']}")
print(f"breakdown tiers={len(d.get('breakdown',[]))}")
s = sum(b["subtotal"] for b in d.get("breakdown", []))
print(f"subtotal_sum={s:.2f}, bill_amount={d['amount']:.2f}, match={abs(s - d['amount']) < 0.02}")
PYEOF

# 6. Pay a bill (模拟 Payment.tsx 确认支付)
echo "=== STEP 6: PAY BILL ==="
echo "--- POST /api/bills/$FIRST_UNPAID_ID/pay (模拟支付)"
PAY_RESP=$(curl -s -X POST "http://localhost:5000/api/bills/$FIRST_UNPAID_ID/pay" \
  -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d '{"method":"wechat"}')
python3 << PYEOF
import sys, json
d = json.loads('''$PAY_RESP''')
p = d.get("payment")
b = d.get("bill")
tx = p.get("transaction_no") if p else None
print(f"transaction_no={tx} (starts with PAY? {tx.startswith('PAY') if tx else False})")
status = b.get("status") if b else None
paid_at = b.get("paid_at") if b else None
print(f"bill.status now={status}, paid_at set={bool(paid_at) if paid_at is not None else None}")
PYEOF

# 7. 刷新 unpaid 列表，确认刚才的账单不在了
echo "=== STEP 7: REFRESH UNPAID LIST ==="
echo "--- GET /api/bills?status=unpaid 再次刷新"
REFRESHED=$(curl -s "http://localhost:5000/api/bills?status=unpaid&per_page=50" -H "$AUTH")
python3 << PYEOF
import sys, json
d = json.loads('''$REFRESHED''')
ids = [b["id"] for b in d["bills"]]
print(f"unpaid count now={len(ids)}")
PYEOF

# 停止后端
pkill -f "python app.py" 2>/dev/null
sleep 1
echo "--- Done ---"
