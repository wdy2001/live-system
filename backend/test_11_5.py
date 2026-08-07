"""任务 11.5 接口逻辑验证 (SQLite 模式佐证功能完整性)"""
import os
import sys
import json

sys.path.insert(0, '/workspace/backend')
os.chdir('/workspace/backend')

from app import create_app
from models import Bill, Payment, Meter

app = create_app()
client = app.test_client()

print("=" * 60)
print("任务 11.5 接口逻辑验证 (SQLite 模式)")
print("=" * 60)

# 登录
r = client.post('/api/auth/login', json={'username':'demo','password':'demo123'})
print(f"\n[1] demo 登录: status={r.status_code}")
d = r.get_json() or {}
token = d.get('token')
print(f"    token 存在: {bool(token)}")
ok_login = r.status_code == 200 and bool(token)
print(f"    => {'PASS' if ok_login else 'FAIL'}")
headers = {'Authorization': f'Bearer {token}'}

# GET /api/bills >= 16 条
r = client.get('/api/bills', headers=headers)
bills = (r.get_json() or {}).get('bills', [])
print(f"\n[2] GET /api/bills: status={r.status_code}, count={len(bills)}")
ok_count = r.status_code == 200 and len(bills) >= 16
print(f"    => {'PASS' if ok_count else 'FAIL'}")

# GET /api/bills?type=water 全为 water
r = client.get('/api/bills?type=water', headers=headers)
wbs = (r.get_json() or {}).get('bills', [])
all_water = all(b.get('type') == 'water' for b in wbs)
print(f"\n[3] GET /api/bills?type=water: status={r.status_code}, count={len(wbs)}, 全water={all_water}")
ok_water = r.status_code == 200 and len(wbs) > 0 and all_water
print(f"    => {'PASS' if ok_water else 'FAIL'}")

# POST /pay 验证三者
with app.app_context():
    unpaid = Bill.query.filter_by(status='unpaid').first()
    unpaid_id = unpaid.id
    old_meter_id = unpaid.meter_id
    old_reading = float(Meter.query.get(old_meter_id).current_reading)
    new_reading = float(unpaid.current_reading)
    print(f"\n[4] 选取 unpaid_id={unpaid_id}, meter_id={old_meter_id}, bill_current_reading={new_reading}, meter.current_reading 支付前={old_reading}")

r = client.post(f'/api/bills/{unpaid_id}/pay', json={'method':'alipay'}, headers=headers)
d = r.get_json() or {}
print(f"    支付请求: status={r.status_code}")

with app.app_context():
    b = Bill.query.get(unpaid_id)
    status_ok = b.status == 'paid'
    p = Payment.query.filter_by(bill_id=unpaid_id).first()
    payment_ok = p is not None
    m = Meter.query.get(old_meter_id)
    meter_ok = float(m.current_reading) == new_reading
    print(f"    支付后验证: bill.status='{b.status}' => {'OK' if status_ok else 'NG'}")
    print(f"                payment 存在 id={p.id if p else None} => {'OK' if payment_ok else 'NG'}")
    print(f"                meter.current_reading={float(m.current_reading)} (期望={new_reading}) => {'OK' if meter_ok else 'NG'}")
ok_pay = (r.status_code == 200) and status_ok and payment_ok and meter_ok
print(f"    => {'PASS' if ok_pay else 'FAIL'}")

print("\n" + "=" * 60)
overall = all([ok_login, ok_count, ok_water, ok_pay])
print(f"任务 11.5 接口逻辑 (SQLite 模式): {'PASS' if overall else 'FAIL'}")
sys.exit(0 if overall else 1)
