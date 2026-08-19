"""TR-11.2 分页异常值 + TR-11.3 越权访问 + TR-11.4 密码哈希 综合验证"""
import os
import sys
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"

PASSED = 0
FAILED = 0

def check(cond, name, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✅ PASS: {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  ❌ FAIL: {name}" + (f"  ({detail})" if detail else ""))

def http(method, path, token=None, json_data=None):
    url = BASE + path
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_data is not None:
        data = json.dumps(json_data).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}

print("\n=== 登录获取 token ===")
_, demo_login = http("POST", "/api/auth/login", json_data={"username": "demo", "password": "demo123"})
DEMO_TOKEN = demo_login["access_token"]
print(f"  DEMO_TOKEN 获取成功, 前缀: {DEMO_TOKEN[:20]}...")

_, userb_reg = http("POST", "/api/auth/register", json_data={
    "username": f"userB_{os.getpid()}",
    "password": "userB123",
    "confirm_password": "userB123",
    "real_name": "User B",
    "phone": "13800000002",
})
USERB_TOKEN = userb_reg["access_token"]
print(f"  USERB_TOKEN 注册成功, 前缀: {USERB_TOKEN[:20]}...")

# ==================== TR-11.2 分页异常值 ====================
print("\n=== TR-11.2 分页异常值 ===\n")

# Test 1: page=0, per_page=100 -> page=1, per_page<=50
print("--- Test 1: page=0&per_page=100 ---")
status1, data1 = http("GET", "/api/bills?page=0&per_page=100", token=DEMO_TOKEN)
check(status1 == 200, f"HTTP 200", f"actual={status1}")
check(data1["page"] == 1, f"实际返回 page=1 (被修正)", f"actual={data1['page']}")
check(data1["per_page"] <= 50, f"per_page 被截断到 ≤50", f"actual={data1['per_page']}")
bills_len1 = len(data1["bills"])
total1 = data1["total"]
check(total1 == 18, f"total=18 (6月×3类)", f"actual={total1}")
check(bills_len1 <= min(50, total1), f"bills.length ≤ min(50,total)", f"bills_len={bills_len1}, total={total1}")

# Test 2: page=1000, per_page=10 -> bills=[], total=18
print("\n--- Test 2: page=1000&per_page=10 ---")
status2, data2 = http("GET", "/api/bills?page=1000&per_page=10", token=DEMO_TOKEN)
check(status2 == 200, f"HTTP 200", f"actual={status2}")
check(len(data2["bills"]) == 0, f"bills=[]", f"actual length={len(data2['bills'])}")
check(data2["total"] == 18, f"total 仍=18", f"actual={data2['total']}")

# ==================== TR-11.3 越权访问矩阵 ====================
print("\n=== TR-11.3 越权访问矩阵 ===\n")

# 先获取 demo 的一条 bill_id 和一条 repair_id
_, demo_bills = http("GET", "/api/bills?per_page=1&status=unpaid", token=DEMO_TOKEN)
demo_bill_id = demo_bills["bills"][0]["id"]
print(f"  demo bill_id = {demo_bill_id}")

_, demo_repairs = http("GET", "/api/repairs", token=DEMO_TOKEN)
demo_repair_id = demo_repairs["repairs"][0]["id"]
print(f"  demo repair_id = {demo_repair_id}")

# Test 1: userB GET demo bill detail -> 403
print(f"\n--- Test 1: userB GET /api/bills/{demo_bill_id} (demo) ---")
s1, d1 = http("GET", f"/api/bills/{demo_bill_id}", token=USERB_TOKEN)
check(s1 == 403, f"GET detail = 403", f"actual={s1}, msg={d1.get('msg','')}")

# Test 2: userB POST demo bill /pay -> 403
print(f"\n--- Test 2: userB POST /api/bills/{demo_bill_id}/pay (demo) ---")
s2, d2 = http("POST", f"/api/bills/{demo_bill_id}/pay", token=USERB_TOKEN, json_data={"method": "alipay"})
check(s2 == 403, f"POST /pay = 403", f"actual={s2}, msg={d2.get('msg','')}")

# Test 3: userB GET demo repair detail -> 403
print(f"\n--- Test 3: userB GET /api/repairs/{demo_repair_id} (demo) ---")
s3, d3 = http("GET", f"/api/repairs/{demo_repair_id}", token=USERB_TOKEN)
check(s3 == 403, f"GET repair detail = 403", f"actual={s3}, msg={d3.get('msg','')}")

# ==================== TR-11.4 密码哈希安全 ====================
print("\n=== TR-11.4 密码哈希安全 ===\n")

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from models import User

app = create_app("development")
with app.app_context():
    demo_user = User.query.filter_by(username="demo").first()
    check(demo_user is not None, "demo 用户存在")
    if demo_user:
        pwd_hash = demo_user.password_hash
        print(f"  password_hash 前缀检查: {pwd_hash[:50]}...")
        check(pwd_hash != "demo123", "非明文 (≠demo123)")
        check("pbkdf2:sha256" in pwd_hash, "包含 pbkdf2:sha256 前缀", f"actual prefix: {pwd_hash[:30]}")
        check(pwd_hash.startswith("pbkdf2:sha256:"), "以 pbkdf2:sha256: 开头")

print(f"\n=== TR-11 综合结果: {PASSED} 通过, {FAILED} 失败 ===")
sys.exit(0 if FAILED == 0 else 1)
