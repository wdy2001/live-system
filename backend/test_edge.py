"""TR-13 边缘情况测试：404 JSON / 重复支付 / 全局 500"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Bill, Payment

results = {}

print("=" * 60)
print("TR-13 错误处理与健壮性测试")
print("=" * 60)

# ====== TR-13.3 全局 500 (先单独测，创建 app 后立即注入测试路由) ======
print("\n--- TR-13.3 全局 500 ---")
app500 = create_app()

with app500.app_context():
    @app500.route('/api/test500')
    def _test_500():
        return 1 / 0

client500 = app500.test_client()
r500 = client500.get('/api/test500')
b500 = r500.get_json(silent=True) or {}
print(f"GET /api/test500 → status={r500.status_code}, body={b500}")
results['13_3_status_500'] = r500.status_code == 500
results['13_3_msg'] = '服务器内部错误' in (b500.get('msg', '') or '')
print(f"  500状态: {results['13_3_status_500']}, msg含服务器内部错误: {results['13_3_msg']}")

# ====== TR-13.1 404 JSON ======
print("\n--- TR-13.1 404 JSON ---")
app = create_app()
client = app.test_client()
resp = client.get('/api/nope')
body = resp.get_json(silent=True) or {}
print(f"GET /api/nope → status={resp.status_code}, body={body}")
results['13_1_status_404'] = resp.status_code == 404
results['13_1_msg'] = '资源不存在' in (body.get('msg', '') or '')
print(f"  13.1 status=404: {results['13_1_status_404']}, msg含'资源不存在': {results['13_1_msg']}")

# ====== 先登录 + 获取 unpaid bill ======
with app.app_context():
    demo = User.query.filter_by(username='demo').first()
    print(f"\ndemo 用户 id={demo.id if demo else None}")
    unpaid = Bill.query.filter_by(status='unpaid').first()
    print(f"unpaid bill id={unpaid.id if unpaid else None}, status={unpaid.status if unpaid else None}")
    unpaid_id = unpaid.id if unpaid else None

client = app.test_client()
login_resp = client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
login_data = login_resp.get_json() or {}
token = login_data.get('token')
print(f"登录 → status={login_resp.status_code}, token存在={bool(token)}")
headers = {'Authorization': f'Bearer {token}'}

# ====== TR-13.2 错误重复支付 ======
print(f"\n--- TR-13.2 重复支付 (unpaid_id={unpaid_id}) ---")
r1 = client.post(f'/api/bills/{unpaid_id}/pay', json={'method': 'wechat'}, headers=headers)
b1 = r1.get_json(silent=True) or {}
print(f"第一次支付 → status={r1.status_code}, body.keys={list(b1.keys())}")
results['13_2_first_200'] = r1.status_code == 200

r2 = client.post(f'/api/bills/{unpaid_id}/pay', json={'method': 'wechat'}, headers=headers)
b2 = r2.get_json(silent=True) or {}
print(f"第二次支付 → status={r2.status_code}, body={b2}")
results['13_2_second_400'] = r2.status_code == 400
results['13_2_msg_paid'] = '已支付' in (b2.get('msg', '') or '')
print(f"  第一次200: {results['13_2_first_200']}, 第二次400: {results['13_2_second_400']}, msg含已支付: {results['13_2_msg_paid']}")

# ====== 汇总 ======
print("\n" + "=" * 60)
print("TR-13.1~13.3 结果汇总")
print("=" * 60)
all_pass = True
for k, v in results.items():
    mark = 'PASS' if v else 'FAIL'
    if not v:
        all_pass = False
    print(f"  {k}: {mark}")
print(f"\nTR-13.1~13.3 总体: {'PASS' if all_pass else 'FAIL'}")
sys.exit(0 if all_pass else 1)
