"""TR-13.2 完整端到端验收脚本（精确覆盖 TR-13.2 + TR-11/12/13 辅助验证）"""
import os
import sys
import random
import string

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from services.billing import calculate_tiered_amount

PASSED = 0
FAILED = 0
ALL = []

def check(cond, name, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        ALL.append(("PASS", name, detail))
        print(f"  ✅ PASS: {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        ALL.append(("FAIL", name, detail))
        print(f"  ❌ FAIL: {name}" + (f"  ({detail})" if detail else ""))

def rand_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

app = create_app("development")
client = app.test_client()

with app.app_context():
    db.drop_all()
    db.create_all()
    from seed import seed as run_seed
    run_seed()

print("\n" + "="*70)
print("TR-13.2 端到端验收 (精确覆盖 TR-13.2 要求)")
print("="*70)

# ============================================================
# 1. 注册新用户 (201 + token)
# ============================================================
print("\n=== 1. 注册新用户 (201 + token) ===")
username = f"u_{rand_suffix()}"
pwd = "Test123456"
r_reg = client.post("/api/auth/register", json={
    "username": username, "password": pwd, "confirm_password": pwd,
    "real_name": "Test", "phone": "13900000001",
})
check(r_reg.status_code == 201, "注册 HTTP 201", f"actual={r_reg.status_code}")
reg_data = r_reg.get_json() or {}
check("access_token" in reg_data and len(reg_data["access_token"]) > 10,
      "注册返回 access_token (非空)")
userB_token = reg_data["access_token"]
userB_headers = {"Authorization": f"Bearer {userB_token}"}

# ============================================================
# 2. 登录 (200 + token)
# ============================================================
print("\n=== 2. 登录 (200 + token) ===")
r_login = client.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
check(r_login.status_code == 200, "登录 HTTP 200", f"actual={r_login.status_code}")
login_data = r_login.get_json() or {}
check("access_token" in login_data and len(login_data["access_token"]) > 10,
      "登录返回 access_token (非空)")
demo_token = login_data["access_token"]
demo_headers = {"Authorization": f"Bearer {demo_token}"}

# ============================================================
# 3. Dashboard 字段齐全
# ============================================================
print("\n=== 3. Dashboard 字段齐全 ===")
r_dash = client.get("/api/dashboard", headers=demo_headers)
check(r_dash.status_code == 200, "GET /api/dashboard HTTP 200")
dash = r_dash.get_json() or {}

check("unpaid_total" in dash, "dashboard 含 unpaid_total")
check("unpaid_count" in dash, "dashboard 含 unpaid_count")
check("repair_stats" in dash, "dashboard 含 repair_stats")
repair_stats = dash.get("repair_stats", {})
check(all(k in repair_stats for k in ["pending", "processing", "resolved"]),
      "repair_stats 含 pending/processing/resolved 键")

check("monthly_usage" in dash, "dashboard 含 monthly_usage")
monthly = dash.get("monthly_usage", [])
check(len(monthly) == 6, f"monthly_usage 长度=6", f"actual={len(monthly)}")

# ============================================================
# 4. 阶梯算法精确验证
# ============================================================
print("\n=== 4. 阶梯算法精确验证 ===")

with app.app_context():
    # 电 250 度 = 150.50
    r_el = calculate_tiered_amount("electricity", 250)
    check(abs(r_el["amount"] - 150.50) < 0.001,
          "电 250 度 = 150.50", f"actual={r_el['amount']}")

    # 水 15 吨 = 55.80
    # 水: 1档 0-12 吨 3.5, 2档 12-24 吨 4.6
    # 12*3.5 + 3*4.6 = 42 + 13.8 = 55.80
    r_wt = calculate_tiered_amount("water", 15)
    check(abs(r_wt["amount"] - 55.80) < 0.001,
          "水 15 吨 = 55.80", f"actual={r_wt['amount']}")

    # 气 350 立方 = 947.20
    # 气: 1档 0-310 2.68, 2档 310-600 2.91
    # 310*2.68 + 40*2.91 = 830.8 + 116.4 = 947.20
    r_gs = calculate_tiered_amount("gas", 350)
    check(abs(r_gs["amount"] - 947.20) < 0.001,
          "气 350 立方 = 947.20", f"actual={r_gs['amount']}")

# ============================================================
# 5. 账单分页: bills.total = 18
# ============================================================
print("\n=== 5. 账单分页 bills.total=18 ===")
r_bills = client.get("/api/bills?page=1&per_page=50", headers=demo_headers)
check(r_bills.status_code == 200, "GET /api/bills HTTP 200")
bills_data = r_bills.get_json() or {}
check(bills_data.get("total") == 18,
      "bills.total = 18", f"actual={bills_data.get('total')}")

# ============================================================
# 6. 账单支付: unpaid -> POST /pay -> status = paid
# ============================================================
print("\n=== 6. 账单支付状态变更 ===")
r_unpaid = client.get("/api/bills?status=unpaid&per_page=1", headers=demo_headers)
unpaid_list = r_unpaid.get_json().get("bills", [])
check(len(unpaid_list) > 0, "存在 unpaid 账单")
if unpaid_list:
    bill_id = unpaid_list[0]["id"]
    check(unpaid_list[0]["status"] == "unpaid",
          f"bill_id={bill_id} status=unpaid 前置条件")
    r_pay = client.post(f"/api/bills/{bill_id}/pay",
                       json={"method": "alipay"}, headers=demo_headers)
    check(r_pay.status_code == 200, "POST /pay HTTP 200")
    after_pay = r_pay.get_json().get("bill", {})
    check(after_pay.get("status") == "paid",
          f"支付后 bill.status=paid",
          f"actual={after_pay.get('status')}")

# ============================================================
# 7. 报修: 创建合法(201); 描述5字(400); 手机号格式错(400)
# ============================================================
print("\n=== 7. 报修接口验证 ===")

# 7a. 描述 5 字 = 400 (需求要求 10-500 字，5字应返回 400)
r_short = client.post("/api/repairs", json={
    "type": "water", "description": "一共5个字",
    "phone": "13900001111", "urgency": "normal",
}, headers=demo_headers)
check(r_short.status_code == 400,
      "报修描述 5 字 -> HTTP 400",
      f"actual={r_short.status_code}, msg={(r_short.get_json()or{}).get('msg','')}")

# 7b. 手机号格式错误 = 400
r_bad_phone = client.post("/api/repairs", json={
    "type": "water", "description": "厨房水龙头漏水需要维修处理谢谢",
    "phone": "1234567", "urgency": "normal",
}, headers=demo_headers)
check(r_bad_phone.status_code == 400,
      "报修手机号格式错 -> HTTP 400",
      f"actual={r_bad_phone.status_code}, msg={(r_bad_phone.get_json()or{}).get('msg','')}")

# 7c. 创建合法工单 = 201
r_good = client.post("/api/repairs", json={
    "type": "water", "description": "厨房水龙头漏水需要维修处理谢谢",
    "phone": "13900001111", "urgency": "normal",
}, headers=demo_headers)
check(r_good.status_code == 201,
      "创建合法报修工单 HTTP 201",
      f"actual={r_good.status_code}")
new_repair = (r_good.get_json() or {}).get("repair", {})
check(new_repair.get("id") is not None and new_repair.get("id") > 0,
      "返回 repair.id>0")
demo_repair_id = new_repair.get("id")

# ============================================================
# 8. 越权: userB 访问 demo bill (403)
# ============================================================
print("\n=== 8. 越权访问验证 ===")

# 获取 demo 的一条 bill id
r_demo_bills = client.get("/api/bills?per_page=1", headers=demo_headers)
demo_bill_id = r_demo_bills.get_json()["bills"][0]["id"]

r_403_bill = client.get(f"/api/bills/{demo_bill_id}", headers=userB_headers)
check(r_403_bill.status_code == 403,
      f"userB 访问 demo bill_id={demo_bill_id} -> HTTP 403",
      f"actual={r_403_bill.status_code}")

r_403_pay = client.post(f"/api/bills/{demo_bill_id}/pay",
                       json={"method": "alipay"}, headers=userB_headers)
check(r_403_pay.status_code == 403,
      f"userB POST demo bill /pay -> HTTP 403",
      f"actual={r_403_pay.status_code}")

r_403_repair = client.get(f"/api/repairs/{demo_repair_id}", headers=userB_headers)
check(r_403_repair.status_code == 403,
      f"userB 访问 demo repair_id={demo_repair_id} -> HTTP 403",
      f"actual={r_403_repair.status_code}")

# ============================================================
# 汇总
# ============================================================
print("\n" + "="*70)
print(f"  TR-13.2 验收结果: {PASSED} 通过, {FAILED} 失败 / 共 {PASSED+FAILED} 项")
print("="*70)

if FAILED > 0:
    print("\n失败用例:")
    for s, n, d in ALL:
        if s == "FAIL":
            print(f"  ❌ {n}  ({d})")
    print()
    sys.exit(1)
else:
    print()
    print("="*50)
    print("  ALL TESTS PASSED 🎉")
    print("="*50)
    sys.exit(0)
